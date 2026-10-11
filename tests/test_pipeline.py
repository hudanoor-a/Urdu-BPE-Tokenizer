"""End-to-end run of the cleaning pipeline and data card on small synthetic sources."""

import gzip
import json
import random
import tempfile
import unittest
from pathlib import Path

from urdu_corpus.clean_pipeline import EOT, SPLITS, load_sources, run
from urdu_corpus.data_card import render

WORDS = "پاکستان شہر خبر حکومت لوگ آج کے میں نے اور کہا سال ملک عوام".split()
BOILERPLATE = "مزید خبریں پڑھیں"
ENGLISH = "This line is entirely English and is dropped by the language filter."


def sentence(rng: random.Random) -> str:
    return " ".join(rng.choice(WORDS) for _ in range(15)) + "۔"


def write_sources(root: Path) -> Path:
    rng = random.Random(0)
    news = [{"text": "\n".join(sentence(rng) for _ in range(4)) + f"\n{BOILERPLATE}\n{ENGLISH}"} for _ in range(120)]
    news[1]["text"] = news[1]["text"].replace("\u06CC", "\u064A")
    news += [news[0], {"text": "مختصر"}]
    (root / "raw").mkdir()
    with (root / "raw" / "news.jsonl").open("w", encoding="utf-8") as f:
        f.writelines(json.dumps(d, ensure_ascii=False) + "\n" for d in news)
    with gzip.open(root / "raw" / "mono.txt.gz", "wt", encoding="utf-8") as f:
        f.writelines(sentence(rng) + "\n" for _ in range(300))
    sources = [
        {"name": "news", "path": "raw/news.jsonl", "fmt": "jsonl", "genre": "news", "mine": True, "url": "u", "licence": "l", "collected": "d"},
        {"name": "mono", "path": "raw/mono.txt.gz", "fmt": "chunk", "chunk": 50, "genre": "mixed", "mine": False, "url": "u", "licence": "l", "collected": "d"},
    ]
    path = root / "sources.json"
    path.write_text(json.dumps(sources), encoding="utf-8")
    return path


class TestCleanPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        cls.sources_path = write_sources(root)
        cls.out = root / "corpus"
        cls.stats = run(cls.sources_path, cls.out)
        cls.text = {name: (cls.out / f"{name}.txt").read_bytes() for name in SPLITS}

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_documents_and_markers(self) -> None:
        totals = self.stats["_totals"]
        for name in SPLITS:
            self.assertEqual(self.text[name].count(EOT.encode()), totals[f"{name}_docs"])
        kept = self.stats["news"]["final_docs"] + self.stats["mono"]["final_docs"]
        self.assertEqual(sum(totals[f"{name}_docs"] for name in SPLITS), kept)
        self.assertEqual(self.stats["mono"]["final_docs"], 6)
        self.assertGreater(totals["train_docs"], totals["val_docs"] + totals["test_docs"])

    def test_cleaning_steps(self) -> None:
        news = self.stats["news"]
        self.assertEqual(news["dup_docs"], 1)
        self.assertEqual(news["lang_removed_docs"], 1)
        self.assertEqual(news["final_docs"], 120)
        corpus = b"".join(self.text.values()).decode("utf-8")
        self.assertNotIn(BOILERPLATE, corpus)
        self.assertNotIn(ENGLISH, corpus)
        self.assertNotIn("\u064A", corpus)
        self.assertNotIn("\r", corpus)

    def test_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as other:
            run(self.sources_path, Path(other))
            for name in SPLITS:
                self.assertEqual((Path(other) / f"{name}.txt").read_bytes(), self.text[name])

    def test_data_card(self) -> None:
        card = render(load_sources(self.sources_path), self.stats)
        for heading in ("## 1. Sources", "## 2. Corpus totals", "## 3. Cleaning steps", "## 4. Normalisation", "## 5. Known gaps"):
            self.assertIn(heading, card)

    def test_duplicate_source_names_rejected(self) -> None:
        path = Path(self.tmp.name) / "dup.json"
        path.write_text(json.dumps([{"name": "a", "path": "x"}, {"name": "a", "path": "y"}]), encoding="utf-8")
        with self.assertRaises(SystemExit):
            load_sources(path)


if __name__ == "__main__":
    unittest.main()
