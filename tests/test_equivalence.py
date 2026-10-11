"""The fast trainer must learn exactly the reference trainer's merges, in the same order.

The sample comparison uses data/sample_1mb.txt (python -m urdu_bpe.make_sample) and
BPE_EQ_MERGES merges (default 1000; the reference needs about 0.2 s per merge on 1 MB).
"""

import os
import unittest
from pathlib import Path

from urdu_bpe import FIRST_MERGE_ID, BPETokenizer
from urdu_bpe.bpe_reference import train_reference, train_reference_text

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample_1mb.txt"
NUM_MERGES = int(os.environ.get("BPE_EQ_MERGES", "1000"))


def fast_merges(text: str, num_merges: int) -> list[tuple[int, int]]:
    tok = BPETokenizer()
    tok.train_text(text, FIRST_MERGE_ID + num_merges)
    return list(tok.merges)


class TestEquivalence(unittest.TestCase):
    def assertSameMerges(self, reference: list, fast: list) -> None:
        for k, (r, f) in enumerate(zip(reference, fast), 1):
            if r != f:
                self.fail(f"first difference at merge {k}: reference {r}, fast {f}")
        self.assertEqual(len(reference), len(fast))

    def test_sanity_check(self) -> None:
        # "aa" occurs 4 times; then (aa, a) and (a, b) tie at 2 and b"aa" > b"a"; then aaab; then four
        # pairs tie at 1 and the greatest as bytes is (b"d", b"aaab") although (aaab, d) has the larger IDs.
        expected = [(97, 97), (257, 97), (258, 98), (100, 259)]
        self.assertEqual(train_reference_text("aaabdaaabac", 4), expected)
        self.assertEqual(fast_merges("aaabdaaabac", 4), expected)

    def test_urdu_word_starts_as_bytes(self) -> None:
        self.assertEqual(len(BPETokenizer().encode("کتاب")), 8)

    def test_special_token_never_merged(self) -> None:
        text = "ab<|endoftext|>ab<|endoftext|>ab"
        self.assertEqual(train_reference_text(text, 10), [(97, 98)])
        self.assertEqual(fast_merges(text, 10), [(97, 98)])

    def test_merges_stay_inside_words(self) -> None:
        tok = BPETokenizer()
        tok.train_text("ab ab ab", FIRST_MERGE_ID + 10)
        self.assertTrue(all(b" " not in tok.vocab[i][1:] for i in tok.merges.values()))

    def test_fast_matches_reference_on_sample(self) -> None:
        if not SAMPLE.is_file():
            self.skipTest(f"{SAMPLE} missing: run python -m urdu_bpe.make_sample")
        reference = train_reference(SAMPLE, NUM_MERGES)
        tok = BPETokenizer()
        tok.train(SAMPLE, FIRST_MERGE_ID + NUM_MERGES)
        self.assertEqual(len(reference), NUM_MERGES)
        self.assertSameMerges(reference, list(tok.merges))


if __name__ == "__main__":
    unittest.main()
