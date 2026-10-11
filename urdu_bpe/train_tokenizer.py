"""Train the tokenizer on train.txt and save it, merges included, as JSON.

Usage:
    python -m urdu_bpe.train_tokenizer [--train corpus/train.txt] [--vocab-size 50000] [--out artifacts/tokenizer.json]
"""

from __future__ import annotations

import argparse
import os
import platform
import time
from pathlib import Path

from .bpe import BPETokenizer
from .pretokenize import FIRST_MERGE_ID


def machine_description() -> str:
    return f"{platform.platform()} | {platform.processor()} | {os.cpu_count()} logical CPUs | Python {platform.python_version()}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--train", type=Path, default=Path("corpus/train.txt"))
    ap.add_argument("--vocab-size", type=int, default=50_000)
    ap.add_argument("--out", type=Path, default=Path("artifacts/tokenizer.json"))
    ap.add_argument("--reference", action="store_true", help="use the slow reference trainer (small files only)")
    args = ap.parse_args()

    machine = machine_description()
    print(f"training on {args.train}: vocab size {args.vocab_size:,} ({args.vocab_size - FIRST_MERGE_ID:,} merges)")
    print(f"machine: {machine}")
    start = time.perf_counter()
    tok = BPETokenizer()
    tok.train(args.train, args.vocab_size, fast=not args.reference, verbose=True)
    elapsed = time.perf_counter() - start

    tok.train_info.update(train_file=args.train.as_posix(), wall_clock_seconds=round(elapsed, 1), machine=machine)
    tok.save(args.out)
    for key in ("distinct_words", "word_occurrences", "count_seconds", "merge_seconds"):
        if key in tok.train_info:
            print(f"{key}: {tok.train_info[key]:,}")
    print(f"merges learned: {len(tok.merges):,} (vocab size {FIRST_MERGE_ID + len(tok.merges):,})")
    print(f"wall-clock time: {elapsed:.1f}s ({elapsed / 3600:.2f} h)")
    print(f"saved {args.out}")


if __name__ == "__main__":
    main()
