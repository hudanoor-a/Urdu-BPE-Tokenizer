"""Q2: tokens per word of this tokenizer, GPT-2 (gpt2) and a modern multilingual tokenizer (o200k_base).

Usage:
    python -m analysis.q2_compare [--tokenizer artifacts/tokenizer.json] [--test corpus/test.txt]

Words are whitespace-separated. "ours + normalize" runs urdu_corpus.normalize first, as the
training text was. Writes analysis/output/q2_compare.md.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path

import tiktoken

from urdu_bpe import EOT_TOKEN, BPETokenizer
from urdu_corpus.normalize import normalize

from .common import md_table, write_output

INPUTS = {
    "news": "وزیراعظم نے آج اسلام آباد میں وفاقی کابینہ کے اجلاس کی صدارت کی جس میں ملک کی معاشی صورتحال "
    "اور مہنگائی پر قابو پانے کے لیے نئے اقدامات کا جائزہ لیا گیا۔",
    "poetry": "ہزاروں خواہشیں ایسی کہ ہر خواہش پہ دم نکلے\nبہت نکلے مرے ارمان لیکن پھر بھی کم نکلے\n"
    "خودی کو کر بلند اتنا کہ ہر تقدیر سے پہلے\nخدا بندے سے خود پوچھے بتا تیری رضا کیا ہے",
    "Urdu + English": "میں نے کل laptop پر Zoom meeting attend کی اور پھر project کی deadline کے بارے میں "
    "manager کو email بھیجی۔",
    "Roman Urdu": "Aap kaise hain? Main theek hoon, shukriya. Kal hum bazaar ja rahe hain, "
    "aap bhi saath chalenge?",
    "numbers and dates": "اجلاس 12 مارچ 2025 کو صبح 10:30 بجے ہوگا، 1,250 افراد شرکت کریں گے اور ٹکٹ "
    "کی قیمت 3,500 روپے ہے۔ رابطہ: 0300-1234567",
    "diacritics": "بِسْمِ اللّٰہِ الرَّحْمٰنِ الرَّحِیْمِ۔ اُردُو ہَماری قَومی زَبان ہے۔",
    "personal names": "محمد علی جناح، علامہ محمد اقبال، فیض احمد فیض، بے نظیر بھٹو، عبدالستار ایدھی "
    "اور ملالہ یوسفزئی",
}


def encoders(tok: BPETokenizer) -> dict[str, Callable[[str], list[int]]]:
    gpt2, o200k = tiktoken.get_encoding("gpt2"), tiktoken.get_encoding("o200k_base")
    return {
        "ours": tok.encode,
        "ours + normalize": lambda text: tok.encode(normalize(text)),
        "gpt2": gpt2.encode_ordinary,
        "o200k_base": o200k.encode_ordinary,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tokenizer", type=Path, default=Path("artifacts/tokenizer.json"))
    ap.add_argument("--test", type=Path, default=Path("corpus/test.txt"))
    args = ap.parse_args()

    test = args.test.read_text(encoding="utf-8").replace(f"{EOT_TOKEN}\n", "")
    texts = {args.test.name: test, **INPUTS}
    enc = encoders(BPETokenizer.load(args.tokenizer))

    rows, totals = [], []
    for name, text in texts.items():
        words = len(text.split())
        counts = {label: len(encode(text)) for label, encode in enc.items()}
        rows.append([name, f"{words:,}"] + [f"{n / words:.2f}" for n in counts.values()])
        if name == args.test.name:
            size = len(text.encode("utf-8"))
            totals = [[label, f"{n:,}", f"{size / n:.2f}", f"{n / counts['ours']:.2f}x"] for label, n in counts.items()]

    path = write_output(
        "q2_compare.md",
        [
            "## Tokens per word\n",
            md_table(["input", "words", *enc], rows),
            f"## {args.test.name} totals\n",
            md_table(["tokenizer", "tokens", "bytes per token", "tokens vs ours"], totals),
        ],
    )
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
