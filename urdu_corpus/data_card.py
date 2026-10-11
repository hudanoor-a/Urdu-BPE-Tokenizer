"""Render the one-page DATA_CARD.md from sources.json and the pipeline's stats.json.

Usage:
    python -m urdu_corpus.data_card [--sources sources.json] [--stats corpus/stats.json] [--out corpus/DATA_CARD.md]
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .clean_pipeline import (
    BOILER_MAX_LEN,
    BOILER_MIN_DOCS,
    EOT,
    LANG_MIN_RATIO,
    MIN_DOC_CHARS,
    SEED,
    SPLIT_FRACTIONS,
    SPLITS,
    load_sources,
)
from .normalize import ZWNJ_POLICY

SELF_COLLECTED_MIN_MB = 50


def mb(n: int) -> str:
    return f"{n / 1e6:,.2f}"


def _sources_section(sources: list[dict], stats: dict) -> list[str]:
    lines = [
        "## 1. Sources\n",
        "| Source | Genre | URL | Licence / terms | Collected | Self-collected | Raw MB | Cleaned MB | Docs |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for s in sources:
        st = stats[s["name"]]
        lines.append(
            f"| {s['name']} | {s['genre']} | {s['url']} | {s['licence']} | {s.get('collected', 'TODO')} | "
            f"{'yes' if s.get('mine') else 'no'} | {mb(st['raw_bytes'])} | {mb(st['final_bytes'])} | {st['final_docs']:,} |"
        )
    raw = sum(stats[s["name"]]["raw_bytes"] for s in sources if s.get("mine"))
    clean = sum(stats[s["name"]]["final_bytes"] for s in sources if s.get("mine"))
    lines.append(
        f"\nSelf-collected by scraping: **{mb(raw)} MB raw, {mb(clean)} MB cleaned** "
        f"(requirement: {SELF_COLLECTED_MIN_MB} MB). Evidence: `raw/scraped/<site>/crawl_log.csv`, "
        "`manifest.csv`, dated `robots_*.txt` and `raw_samples/`.\n"
    )
    return lines


def _totals_section(totals: dict) -> list[str]:
    lines = ["## 2. Corpus totals\n", "| Split | Docs | MB | Words |", "|---|---|---|---|"]
    for name in SPLITS:
        lines.append(f"| {name}.txt | {totals[name + '_docs']:,} | {mb(totals[name + '_bytes'])} | {totals[name + '_words']:,} |")
    total = {k: sum(totals[f"{n}_{k}"] for n in SPLITS) for k in ("docs", "bytes", "words")}
    lines.append(f"| **total** | {total['docs']:,} | {mb(total['bytes'])} | {total['words']:,} |")
    split = "/".join(f"{f * 100:g}" for f in SPLIT_FRACTIONS)
    lines.append(
        f"\nUnique words (regex `\\w+`): **{totals['unique_words']:,}**. Split {split} by document "
        f"(seed {SEED}), `{EOT}` after each document. MB = 10^6 bytes of UTF-8 text.\n"
    )
    return lines


def _cleaning_section(stats: dict) -> list[str]:
    s = Counter()
    for st in stats.values():
        s.update(st)
    steps = [
        ("1 Extract", "URLs and e-mails removed (HTML was reduced to article text by trafilatura at scrape time)", "raw_bytes", "extract_bytes"),
        ("2 Normalise", "`normalize()`, section 4", "extract_bytes", "norm_bytes"),
        ("3 Language filter", f"drop lines with < {LANG_MIN_RATIO:.0%} Urdu-script letters, then docs < {MIN_DOC_CHARS} chars", "norm_bytes", "lang_bytes"),
        ("4a Exact dedup", f"{s['dup_docs']:,} duplicate documents (MD5 of cleaned text)", "lang_bytes", "dedup_bytes"),
        ("4b Boilerplate", f"lines <= {BOILER_MAX_LEN} chars found in >= {BOILER_MIN_DOCS} docs", "dedup_bytes", "final_bytes"),
    ]
    lines = ["## 3. Cleaning steps\n", "| Step | What it does | MB before | MB after | Removed |", "|---|---|---|---|---|"]
    for name, what, before, after in steps:
        a, b = s[before], s[after]
        lines.append(f"| {name} | {what} | {mb(a)} | {mb(b)} | {(a - b) / a * 100 if a else 0:.1f}% |")
    lines.append(
        f"\nDocuments: {s['raw_docs']:,} read, {s['lang_removed_docs']:,} too short or not Urdu, "
        f"{s['dup_docs']:,} duplicates, {s['boiler_removed_docs']:,} too short after boilerplate removal, "
        f"{s['final_docs']:,} kept.\n"
    )
    return lines


def _normalisation_section(stats: dict) -> list[str]:
    zwnj = {name: st["zwnj_raw"] for name, st in stats.items() if st["zwnj_raw"]}
    zwnj_where = ", ".join(f"{n} ({c:,})" for n, c in zwnj.items()) or "no source"
    return [
        "## 4. Normalisation decisions\n",
        "- NFKC first (folds presentation forms and ligatures). Arabic yeh U+064A and alef maksura U+0649 to U+06CC; "
        "Arabic kaf U+0643 and swash kaf U+06AA to U+06A9; Arabic heh U+0647 to gol heh U+06C1 (do-chashmi heh U+06BE kept apart); "
        "teh marbuta U+0629 to U+06C3.",
        "- Tatweel and harakat U+064B-U+0652 removed: they are used inconsistently and would split one word into several spellings. "
        "Superscript alef U+0670 and honorific signs U+0610-U+0615 are kept as part of the spelling.",
        "- Digits: Arabic-Indic and Extended Arabic-Indic digits mapped to ASCII 0-9.",
        f"- ZWNJ U+200C: **{ZWNJ_POLICY}**. Only {zwnj_where} contained ZWNJ, so its use is inconsistent across sources; "
        "keeping it would give one word two byte sequences and two sets of tokens.",
        "- ZWJ, direction marks, bidi controls, BOM, soft hyphen and control characters removed; runs of spaces and "
        "non-breaking spaces collapsed to one space; line breaks unified to LF; empty lines dropped.\n",
    ]


def _gaps_section(sources: list[dict], stats: dict) -> list[str]:
    genre_bytes: Counter = Counter()
    for s in sources:
        genre_bytes[s["genre"]] += stats[s["name"]]["final_bytes"]
    total = sum(genre_bytes.values()) or 1
    shares = "; ".join(f"{g} {b / total:.1%}" for g, b in genre_bytes.most_common())
    return [
        "## 5. Known gaps and biases\n",
        f"- Genre shares by cleaned bytes: {shares}. The mixed-domain UFAL corpus dominates and its domains are unlabelled.",
        "- Time skew: UFAL was released in 2014 and Wikipedia is the 2023-11-01 snapshot; only the scraped news covers recent events.",
        "- UFAL is one sentence per line; every 50 lines form a pseudo-document, so its document boundaries are artificial.",
        "- Formal written Urdu only: social media, chat, Roman Urdu and poetry are nearly absent; English-heavy lines are filtered out.",
        "- Deduplication is exact only: near-duplicate news stories and templated Wikipedia stubs remain.",
    ]


def render(sources: list[dict], stats: dict) -> str:
    per_source = {name: Counter(st) for name, st in stats.items() if name != "_totals"}
    for s in sources:
        per_source.setdefault(s["name"], Counter())
    lines = ["# DATA CARD: Urdu corpus\n"]
    lines += _sources_section(sources, per_source)
    lines += _totals_section(Counter(stats["_totals"]))
    lines += _cleaning_section(per_source)
    lines += _normalisation_section(per_source)
    lines += _gaps_section(sources, per_source)
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sources", type=Path, default=Path("sources.json"))
    ap.add_argument("--stats", type=Path, default=Path("corpus/stats.json"))
    ap.add_argument("--out", type=Path, default=Path("corpus/DATA_CARD.md"))
    args = ap.parse_args()
    stats = json.loads(args.stats.read_text(encoding="utf-8"))
    args.out.write_text(render(load_sources(args.sources), stats), encoding="utf-8", newline="\n")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
