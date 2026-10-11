"""Convert Urdu Wikipedia parquet shards to JSONL for the cleaning pipeline.

The shards come from https://huggingface.co/datasets/wikimedia/wikipedia/tree/main/20231101.ur
(article text already extracted from the dump, so wiki markup is gone).

Usage:
    python -m urdu_corpus.wiki_to_jsonl [--src raw/wiki] [--out raw/urwiki.jsonl]
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterator
from pathlib import Path

import pyarrow.parquet as pq


def iter_articles(paths: list[Path]) -> Iterator[tuple[str, str]]:
    """Stream (title, text) pairs batch by batch, without loading whole shards."""
    for path in paths:
        for batch in pq.ParquetFile(path).iter_batches(columns=["title", "text"]):
            yield from zip(batch.column("title").to_pylist(), batch.column("text").to_pylist())


def convert(paths: list[Path], out: Path) -> tuple[int, int]:
    out.parent.mkdir(parents=True, exist_ok=True)
    n = size = 0
    with out.open("w", encoding="utf-8", newline="\n") as f:
        for title, text in iter_articles(paths):
            if text and text.strip():
                f.write(json.dumps({"title": title, "text": text}, ensure_ascii=False) + "\n")
                n += 1
                size += len(text.encode("utf-8"))
    return n, size


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", type=Path, default=Path("raw/wiki"), help="folder with the .parquet shards")
    ap.add_argument("--out", type=Path, default=Path("raw/urwiki.jsonl"))
    args = ap.parse_args()
    shards = sorted(args.src.glob("*.parquet"))
    if not shards:
        raise SystemExit(f"no .parquet files in {args.src}")
    n, size = convert(shards, args.out)
    print(f"wrote {n} articles ({size / 1e6:.1f} MB of text) to {args.out}")


if __name__ == "__main__":
    main()
