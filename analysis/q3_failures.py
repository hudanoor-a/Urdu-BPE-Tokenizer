"""Q3: three inputs the tokenizer handles badly, with their segmentation.

Usage:
    python -m analysis.q3_failures [--tokenizer artifacts/tokenizer.json]

Writes analysis/output/q3_failures.md.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import tiktoken

from urdu_bpe import BPETokenizer
from urdu_corpus.normalize import normalize

from .common import md_table, show, write_output

CASES = {
    "diacritics (harakat)": "اُردُو ہَماری قَومی زَبان ہے",
    "Roman Urdu": "Main theek hoon, shukriya. Kal hum bazaar ja rahe hain.",
    "Arabic code points and Urdu digits": "پا\u0643ستان \u0643\u064A ح\u0643ومت نے ۱۴ اگست \u0643و چھٹ\u064A \u0643ا اعلان \u0643\u064Aا",
}


def segmentation(tok: BPETokenizer, text: str) -> str:
    return " · ".join(show(tok.vocab[i]) for i in tok.encode(text))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tokenizer", type=Path, default=Path("artifacts/tokenizer.json"))
    args = ap.parse_args()

    tok = BPETokenizer.load(args.tokenizer)
    o200k = tiktoken.get_encoding("o200k_base")
    rows, details = [], []
    for name, text in CASES.items():
        words = len(text.split())
        ours, fixed = tok.encode(text), tok.encode(normalize(text))
        rows.append([name, words, len(ours), f"{len(ours) / words:.2f}", f"{len(fixed) / words:.2f}", f"{len(o200k.encode_ordinary(text)) / words:.2f}"])
        details += [f"**{name}**\n", f"- ours: {segmentation(tok, text)}", f"- ours + normalize: {segmentation(tok, normalize(text))}\n"]

    path = write_output(
        "q3_failures.md",
        [
            "## Tokens per word on the three inputs\n",
            md_table(["input", "words", "ours tokens", "ours", "ours + normalize", "o200k_base"], rows),
            "## Segmentation (tokens separated by ·, space shown as ␣)\n",
            *details,
        ],
    )
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
