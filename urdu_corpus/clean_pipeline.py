"""Cleaning pipeline: extract, normalise, filter non-Urdu lines, deduplicate, split 98/1/1.

Usage:
    python -m urdu_corpus.clean_pipeline [--sources sources.json] [--out corpus]

Pass 1 cleans every document, drops exact duplicates and counts short lines across documents.
Pass 2 removes boilerplate lines (short lines seen in many documents) and splits by document
with a fixed seed. Writes <out>/train.txt, val.txt, test.txt (each document followed by
<|endoftext|>) and <out>/stats.json; render the data card with urdu_corpus.data_card.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from collections.abc import Iterator
from itertools import accumulate
from pathlib import Path
from typing import TextIO

from .normalize import normalize

SEED = 42
SPLITS = ("train", "val", "test")
SPLIT_FRACTIONS = (0.98, 0.01, 0.01)
LANG_MIN_RATIO = 0.5
MIN_DOC_CHARS = 100
BOILER_MIN_DOCS = 50
BOILER_MAX_LEN = 150
EOT = "<|endoftext|>"
STAT_KEYS = (
    "raw_docs", "raw_bytes", "zwnj_raw", "extract_bytes", "norm_bytes", "lang_removed_docs", "lang_docs", "lang_bytes",
    "dup_docs", "dedup_docs", "dedup_bytes", "boiler_removed_docs", "final_docs", "final_bytes",
)

_URL = re.compile(r"https?://\S+|www\.\S+|\S+@\S+\.\S+")
_NON_LETTER = re.compile(r"[\W\d_]+")
_NON_URDU_LETTER = re.compile(r"[^\u0621-\u064A\u066E-\u06D3\u06D5\u06FA-\u06FF\u0750-\u077F]+")
_WORD = re.compile(r"\w+")

Stats = dict[str, Counter]


def load_sources(path: Path) -> list[dict]:
    """Read sources.json; each "path" is resolved relative to the file itself."""
    sources = json.loads(path.read_text(encoding="utf-8"))
    names = [s["name"] for s in sources]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        raise SystemExit(f"duplicate source names in {path}: {duplicates}")
    for s in sources:
        s["path"] = path.parent / s["path"]
    return sources


def utf8_size(text: str) -> int:
    return len(text.encode("utf-8"))


def _open_text(path: Path) -> TextIO:
    opener = gzip.open if path.suffix == ".gz" else open
    return opener(path, "rt", encoding="utf-8", errors="replace")


def _jsonl_texts(f: TextIO, src: dict) -> Iterator[str]:
    field, good, bad = src.get("field", "text"), 0, 0
    for line in f:
        line = line.strip().lstrip("\uFEFF")
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            obj = None
        if not isinstance(obj, dict):
            bad += 1
            continue
        good += 1
        yield obj.get(field, "")
    if bad:
        print(f"  WARNING {src['name']}: skipped {bad} lines that are not JSON objects")
    if not good:
        raise SystemExit(f"{src['name']}: no JSON objects in {src['path']}")


def _line_chunks(f: TextIO, size: int) -> Iterator[str]:
    """Group non-empty lines of a sentence-per-line corpus into pseudo-documents."""
    buf: list[str] = []
    for line in f:
        if line.strip():
            buf.append(line.rstrip("\n"))
            if len(buf) >= size:
                yield "\n".join(buf)
                buf = []
    if buf:
        yield "\n".join(buf)


def iter_docs(src: dict) -> Iterator[str]:
    """Raw documents of one source. fmt "jsonl": one JSON object per line; "chunk": N lines per document."""
    with _open_text(src["path"]) as f:
        if src["fmt"] == "jsonl":
            yield from _jsonl_texts(f, src)
        elif src["fmt"] == "chunk":
            yield from _line_chunks(f, src.get("chunk", 50))
        else:
            raise SystemExit(f"{src['name']}: unknown fmt {src['fmt']!r}")


def is_urdu_line(line: str) -> bool:
    """At least LANG_MIN_RATIO of the letters are Urdu/Arabic-script, so light code-mixing survives."""
    letters = len(_NON_LETTER.sub("", line))
    return letters > 0 and len(_NON_URDU_LETTER.sub("", line)) / letters >= LANG_MIN_RATIO


def is_boilerplate(line: str, line_docs: Counter) -> bool:
    return len(line) <= BOILER_MAX_LEN and line_docs[hash(line)] >= BOILER_MIN_DOCS


def pass1(sources: list[dict], work_path: Path, stats: Stats) -> Counter:
    """Extract, normalise, filter and exact-dedup; returns in how many documents each short line occurs."""
    seen: set[bytes] = set()
    line_docs: Counter = Counter()
    with work_path.open("w", encoding="utf-8", newline="\n") as out:
        for src in sources:
            st = stats[src["name"]]
            print(f"[pass 1] {src['name']}", flush=True)
            for raw in iter_docs(src):
                st["raw_docs"] += 1
                st["raw_bytes"] += utf8_size(raw)
                st["zwnj_raw"] += raw.count("\u200C")
                text = _URL.sub(" ", raw)
                st["extract_bytes"] += utf8_size(text)
                text = normalize(text)
                st["norm_bytes"] += utf8_size(text)
                text = "\n".join(line for line in text.split("\n") if is_urdu_line(line))
                if len(text) < MIN_DOC_CHARS:
                    st["lang_removed_docs"] += 1
                    continue
                st["lang_docs"] += 1
                st["lang_bytes"] += utf8_size(text)
                digest = hashlib.md5(text.encode("utf-8")).digest()
                if digest in seen:
                    st["dup_docs"] += 1
                    continue
                seen.add(digest)
                st["dedup_docs"] += 1
                st["dedup_bytes"] += utf8_size(text)
                line_docs.update(hash(line) for line in set(text.split("\n")) if len(line) <= BOILER_MAX_LEN)
                out.write(json.dumps({"s": src["name"], "t": text}, ensure_ascii=False) + "\n")
            if st["raw_docs"] and not st["lang_docs"]:
                print(f"  WARNING {src['name']}: every document was dropped by the language/length filter")
    return line_docs


def pass2(work_path: Path, line_docs: Counter, out_dir: Path, stats: Stats) -> Counter:
    """Remove boilerplate lines and write each document to train/val/test; returns corpus totals."""
    rng = random.Random(SEED)
    bounds = list(accumulate(SPLIT_FRACTIONS))
    totals: Counter = Counter()
    vocabulary: set[str] = set()
    files = {name: (out_dir / f"{name}.txt").open("w", encoding="utf-8", newline="\n") for name in SPLITS}
    try:
        with work_path.open(encoding="utf-8") as f:
            for record in map(json.loads, f):
                st = stats[record["s"]]
                text = "\n".join(line for line in record["t"].split("\n") if not is_boilerplate(line, line_docs))
                if len(text) < MIN_DOC_CHARS:
                    st["boiler_removed_docs"] += 1
                    continue
                st["final_docs"] += 1
                st["final_bytes"] += utf8_size(text)
                r = rng.random()
                split = next((name for name, b in zip(SPLITS, bounds) if r < b), SPLITS[-1])
                files[split].write(f"{text}\n{EOT}\n")
                words = _WORD.findall(text)
                totals[f"{split}_docs"] += 1
                totals[f"{split}_bytes"] += utf8_size(text)
                totals[f"{split}_words"] += len(words)
                vocabulary.update(words)
    finally:
        for fh in files.values():
            fh.close()
    totals["unique_words"] = len(vocabulary)
    return totals


def run(sources_path: Path, out_dir: Path) -> dict:
    sources = []
    for src in load_sources(sources_path):
        if src["path"].exists():
            sources.append(src)
        else:
            print(f"WARNING: skipping {src['name']}, missing {src['path']}")
    if not sources:
        raise SystemExit("no input files found")
    out_dir.mkdir(parents=True, exist_ok=True)
    stats: Stats = defaultdict(Counter)
    work_path = out_dir / "_stage1.jsonl"
    try:
        line_docs = pass1(sources, work_path, stats)
        print("[pass 2] boilerplate removal and split", flush=True)
        totals = pass2(work_path, line_docs, out_dir, stats)
    finally:
        work_path.unlink(missing_ok=True)
    result = {s["name"]: {k: stats[s["name"]][k] for k in STAT_KEYS} for s in sources} | {"_totals": dict(totals)}
    (out_dir / "stats.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sources", type=Path, default=Path("sources.json"))
    ap.add_argument("--out", type=Path, default=Path("corpus"))
    args = ap.parse_args()
    totals = run(args.sources, args.out)["_totals"]
    print(", ".join(f"{name}: {totals.get(name + '_docs', 0)} docs" for name in SPLITS))
    print(f"wrote {args.out}/train.txt, val.txt, test.txt and stats.json")


if __name__ == "__main__":
    main()
