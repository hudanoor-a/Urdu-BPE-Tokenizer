"""Q1: what did the merges learn?

Usage:
    python -m analysis.q1_merges [--tokenizer artifacts/tokenizer.json] [--words corpus/val.txt]

Writes analysis/output/q1_merges.md: merges 1-50, every 5,000th merge, which early merges rebuild
a two-byte character or are not valid UTF-8, the first whole word, and the 20 longest tokens.
A token is a whole word when, without its leading space, it is at least two letters long and
occurs at least MIN_WORD_COUNT times as a complete word (regex \\w+) in --words.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

from urdu_bpe import FIRST_MERGE_ID, BPETokenizer

from .common import md_table, show, write_output

FIRST_N = 50
EVERY = 5_000
LONGEST = 20
MIN_WORD_COUNT = 100


def classify(pair: tuple[int, int], token: bytes, words: Counter) -> str:
    try:
        text = token.decode("utf-8")
    except UnicodeDecodeError:
        return "not valid UTF-8"
    if len(text) == 1 and len(token) == 2 and max(pair) < 256:
        return "char rebuilt"
    if is_whole_word(text, words):
        return "whole word"
    return "valid"


def is_whole_word(text: str, words: Counter) -> bool:
    word = text.lstrip(" ")
    return len(word) >= 2 and word.isalpha() and words[word] >= MIN_WORD_COUNT


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tokenizer", type=Path, default=Path("artifacts/tokenizer.json"))
    ap.add_argument("--words", type=Path, default=Path("corpus/val.txt"))
    args = ap.parse_args()

    tok = BPETokenizer.load(args.tokenizer)
    words = Counter(re.findall(r"\w+", args.words.read_text(encoding="utf-8")))
    merges = list(tok.merges.items())

    def row(k: int) -> list:
        pair, new_id = merges[k - 1]
        token = tok.vocab[new_id]
        return [k, f"{show(tok.vocab[pair[0]])} + {show(tok.vocab[pair[1]])}", show(token), len(token), classify(pair, token, words)]

    first = [row(k) for k in range(1, FIRST_N + 1)]
    half = FIRST_N // 2
    brief = [[r[0], r[2], r[4]] for r in first]
    grid = [left + right for left, right in zip(brief[:half], brief[half:])]
    later = [row(k) for k in range(EVERY, len(merges) + 1, EVERY)]

    rebuilt = [f"{r[0]} {r[2]}" for r in first if r[4] == "char rebuilt"]
    invalid = [f"{r[0]} {r[2]}" for r in first if r[4] == "not valid UTF-8"]
    whole = [(k, tok.vocab[i]) for k, (_, i) in enumerate(merges, 1) if is_whole_word(tok.vocab[i].decode("utf-8", errors="replace"), words)]
    first_words = [[k, show(t), words[t.decode("utf-8").lstrip(" ")]] for k, t in whole[:5]]

    longest = sorted(tok.merges.values(), key=lambda i: (-len(tok.vocab[i]), i))[:LONGEST]
    long_rows = [
        [rank, i - FIRST_MERGE_ID + 1, show(tok.vocab[i]), len(tok.vocab[i]), len(tok.vocab[i].decode("utf-8", errors="replace"))]
        for rank, i in enumerate(longest, 1)
    ]

    path = write_output(
        "q1_merges.md",
        [
            f"## Merges 1-{FIRST_N}\n",
            md_table(["#", "token", "type", "#", "token", "type"], grid),
            f"## Every {EVERY:,}th merge\n",
            md_table(["merge", "pair", "token", "bytes", "type"], later),
            f"## Merges 1-{FIRST_N} by type\n",
            f"- two-byte character rebuilt ({len(rebuilt)}): {', '.join(rebuilt)}",
            f"- not valid UTF-8 ({len(invalid)}): {', '.join(invalid)}\n",
            f"## First whole words (>= 2 letters, >= {MIN_WORD_COUNT} occurrences in {args.words.name})\n",
            md_table(["merge", "token", f"count in {args.words.name}"], first_words),
            f"## {LONGEST} longest tokens\n",
            md_table(["rank", "merge", "token", "bytes", "chars"], long_rows),
        ],
    )
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
