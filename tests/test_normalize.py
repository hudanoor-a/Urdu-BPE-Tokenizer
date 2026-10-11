import unittest

from urdu_corpus.normalize import normalize


class TestNormalize(unittest.TestCase):
    def test_letter_variants(self) -> None:
        self.assertEqual(normalize("\u0643تاب"), "\u06A9تاب")
        self.assertEqual(normalize("\u064A\u06C1 \u0649\u06C1"), "\u06CC\u06C1 \u06CC\u06C1")
        self.assertEqual(normalize("\u0647ے"), "\u06C1ے")
        self.assertEqual(normalize("بھائ\u06CC"), "بھائ\u06CC")
        self.assertEqual(normalize("ۂ"), "ۂ")

    def test_presentation_forms(self) -> None:
        self.assertEqual(normalize("ﻻ"), "لا")
        self.assertEqual(normalize("ﷲ"), "الل\u06C1")

    def test_removed_marks(self) -> None:
        self.assertEqual(normalize("اردـو"), "اردو")
        self.assertEqual(normalize("اُردُو"), "اردو")
        self.assertEqual(normalize("\uFEFFعلم\u200F"), "علم")

    def test_digits(self) -> None:
        self.assertEqual(normalize("١٢٣ ۴۵۶ 789"), "123 456 789")

    def test_whitespace(self) -> None:
        self.assertEqual(normalize("a\u00A0\u00A0b   c"), "a b c")
        self.assertEqual(normalize("a \r\n\n\n b\rc"), "a\nb\nc")

    def test_zwnj_policies(self) -> None:
        word = "م\u06CC\u200Cخوا\u06C1م"
        self.assertEqual(normalize(word), word.replace("\u200C", ""))
        self.assertEqual(normalize(word, "keep_between_letters"), word)
        self.assertEqual(normalize("\u06C1ے\u200C ۔", "keep_between_letters"), "\u06C1ے ۔")
        with self.assertRaises(ValueError):
            normalize(word, "keep")


if __name__ == "__main__":
    unittest.main()
