"""decode(encode(text)) == text for every kind of input.

Uses artifacts/tokenizer.json when present, otherwise 500 merges trained on data/sample_1mb.txt.
"""

import tempfile
import unittest
from pathlib import Path

from urdu_bpe import EOT_ID, FIRST_MERGE_ID, BPETokenizer

ROOT = Path(__file__).resolve().parents[1]
TOKENIZER = ROOT / "artifacts" / "tokenizer.json"
SAMPLE = ROOT / "data" / "sample_1mb.txt"

CASES = {
    "empty": "",
    "english": "The quick brown fox jumps over the lazy dog. It's 2026!",
    "emoji": "Hello 👋🏽 world 🇵🇰 ❤️ 👨\u200D👩\u200D👧",
    "newlines": "line one\nline two\r\n\n\tindented\n   \n",
    "urdu": "پاکستان کا دارالحکومت اسلام آباد ہے۔",
    "urdu_diacritics": "بِسْمِ اللّٰہِ الرَّحْمٰنِ الرَّحِیْمِ",
    "zwnj_and_digits": "می\u200Cخواہم ۱۲۳ اور 456 ، ؟",
    "unnormalised": "\u0643تاب \u064A\u06C1 \u0647ے",
    "special_token": "پہلا<|endoftext|>دوسرا<|endoftext|>",
    "lone_surrogate": "a\uD800b",
}


class TestRoundtrip(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if TOKENIZER.is_file():
            cls.tok = BPETokenizer.load(TOKENIZER)
        else:
            cls.tok = BPETokenizer()
            if SAMPLE.is_file():
                cls.tok.train(SAMPLE, FIRST_MERGE_ID + 500)
            else:
                cls.tok.train_text("\n".join(CASES.values()), FIRST_MERGE_ID + 50)

    def test_roundtrip(self) -> None:
        for name, text in CASES.items():
            with self.subTest(name=name):
                self.assertEqual(self.tok.decode(self.tok.encode(text)), text)

    def test_special_token(self) -> None:
        self.assertEqual(self.tok.encode(""), [])
        self.assertEqual(self.tok.encode("<|endoftext|>"), [EOT_ID])
        self.assertEqual(self.tok.encode("a<|endoftext|>b").count(EOT_ID), 1)

    def test_save_load(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "tokenizer.json"
            self.tok.save(path)
            again = BPETokenizer.load(path)
        self.assertEqual(again.merges, self.tok.merges)
        self.assertEqual(again.encode(CASES["urdu"]), self.tok.encode(CASES["urdu"]))


if __name__ == "__main__":
    unittest.main()
