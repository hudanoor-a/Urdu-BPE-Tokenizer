"""Polite, resumable scraper for Urdu news sites (the self-collected part of the corpus).

Usage:
    python -m urdu_corpus.scrape --site jang --contact you@example.com [--limit N] [--out raw/scraped]

Writes to <out>/<site>/:
    docs.jsonl        one {"url", "title", "date", "text"} object per article
    manifest.csv      one row per saved article (evidence of collection)
    crawl_log.csv     every request with status and reason (also the resume state)
    robots_<date>.txt copy of robots.txt at crawl time
    raw_samples/      raw HTML of the first 10 and every 200th fetched page
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
import trafilatura

DELAY = 1.5
MIN_CHARS = 300
MIN_ARABIC_RATIO = 0.6
RAW_SAMPLE_EVERY = 200

SITES = {
    "independent": dict(template="https://www.independenturdu.com/node/{id}", start=188177, stop=100000, step=-1, target_mb=70),
    "express_live": dict(template="https://www.express.pk/live-blog/{id}", start=1, stop=61, step=1, target_mb=15),
    "jang": dict(template="https://jang.com.pk/news/{id}", start=1622980, stop=1400000, step=-1, target_mb=40),
}

LOG_HEADER = ["timestamp", "url", "status", "bytes", "chars", "note"]
MANIFEST_HEADER = ["url", "title", "date", "chars", "utf8_bytes", "arabic_ratio"]

_ARABIC = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")
_LETTER = re.compile(r"[^\W\d_]")


def arabic_ratio(text: str) -> float:
    letters = _LETTER.findall(text)
    return sum(1 for c in letters if _ARABIC.match(c)) / len(letters) if letters else 0.0


def append_csv(path: Path, header: list[str], row: list) -> None:
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if new:
            writer.writerow(header)
        writer.writerow(row)


def load_robots(session: requests.Session, base_url: str, out: Path) -> RobotFileParser:
    """Fetch robots.txt, keep a dated copy, and return a parser (401/403 means disallow all)."""
    resp = session.get(base_url + "/robots.txt", timeout=30)
    (out / f"robots_{date.today()}.txt").write_text(resp.text, encoding="utf-8")
    rp = RobotFileParser()
    if resp.status_code in (401, 403):
        rp.disallow_all = True
    else:
        rp.parse(resp.text.splitlines())
    return rp


def fetch(session: requests.Session, url: str, retries: int = 3) -> requests.Response | None:
    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, timeout=30)
        except requests.RequestException:
            time.sleep(5 * attempt)
            continue
        if resp.status_code not in (429, 503):
            return resp
        time.sleep(10 * attempt)
    return None


def extract(html: bytes) -> tuple[str, str, str]:
    """Main article text (menus, adverts and share buttons removed), title and date."""
    text = trafilatura.extract(html, include_comments=False, include_tables=False, include_images=False, favor_precision=True)
    meta = trafilatura.extract_metadata(html)
    return text or "", (meta and meta.title) or "", (meta and meta.date) or ""


def crawl(site: str, contact: str, out_root: Path, limit: int | None = None) -> None:
    cfg = SITES[site]
    out = out_root / site
    (out / "raw_samples").mkdir(parents=True, exist_ok=True)
    log_path, manifest_path, docs_path = out / "crawl_log.csv", out / "manifest.csv", out / "docs.jsonl"

    def log(url: str, status, nbytes: int = 0, chars: int = 0, note: str = "") -> None:
        append_csv(log_path, LOG_HEADER, [datetime.now(timezone.utc).isoformat(timespec="seconds"), url, status, nbytes, chars, note])

    session = requests.Session()
    session.headers["User-Agent"] = f"UrduTokenizerCourseBot/1.0 (student project; contact: {contact})"
    agent = session.headers["User-Agent"]
    rp = load_robots(session, "{0.scheme}://{0.netloc}".format(urlparse(cfg["template"])), out)
    delay = max(DELAY, rp.crawl_delay(agent) or 0)

    done = set()
    if log_path.exists():
        with log_path.open(encoding="utf-8", newline="") as f:
            done = {row["url"] for row in csv.DictReader(f)}
    saved_bytes = docs_path.stat().st_size if docs_path.exists() else 0
    target = cfg["target_mb"] * 1024 * 1024
    print(f"{site}: delay {delay}s, {len(done)} URLs already processed, {saved_bytes / 1e6:.1f} MB saved")

    fetched = 0
    for page_id in range(cfg["start"], cfg["stop"], cfg["step"]):
        if saved_bytes >= target or (limit and fetched >= limit):
            break
        url = cfg["template"].format(id=page_id)
        if url in done:
            continue
        if not rp.can_fetch(agent, url):
            log(url, "SKIP", note="disallowed by robots.txt")
            continue

        time.sleep(delay)
        resp = fetch(session, url)
        fetched += 1
        if resp is None:
            log(url, "ERR", note="gave up after retries")
            continue
        if resp.status_code != 200:
            log(url, resp.status_code, len(resp.content), note="non-200")
            continue

        html = resp.content
        if fetched <= 10 or fetched % RAW_SAMPLE_EVERY == 0:
            (out / "raw_samples" / f"page_{page_id}.html").write_bytes(html)
        text, title, published = extract(html)
        if len(text) < MIN_CHARS:
            log(url, 200, len(html), len(text), "too short / no text")
            continue
        ratio = arabic_ratio(text)
        if ratio < MIN_ARABIC_RATIO:
            log(url, 200, len(html), len(text), f"not urdu (ratio {ratio:.2f})")
            continue

        line = json.dumps({"url": url, "title": title, "date": published, "text": text}, ensure_ascii=False) + "\n"
        with docs_path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(line)
        saved_bytes += len(line.encode("utf-8"))
        append_csv(manifest_path, MANIFEST_HEADER, [url, title, published, len(text), len(text.encode("utf-8")), f"{ratio:.3f}"])
        log(url, 200, len(html), len(text), "saved")
        if fetched % 100 == 0:
            print(f"{fetched} fetched, {saved_bytes / 1e6:.1f} MB saved")

    print(f"done: {saved_bytes / 1e6:.1f} MB in {docs_path}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site", required=True, choices=SITES)
    ap.add_argument("--contact", required=True, help="e-mail address put in the User-Agent")
    ap.add_argument("--limit", type=int, help="maximum pages to fetch in this run")
    ap.add_argument("--out", type=Path, default=Path("raw/scraped"))
    args = ap.parse_args()
    crawl(args.site, args.contact, args.out, args.limit)


if __name__ == "__main__":
    main()
