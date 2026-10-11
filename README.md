# Urdu BPE tokenizer from scratch (CS 417, Assignment 1)

A 1.09 GB cleaned Urdu corpus (Part A) and a byte-level BPE tokenizer with a 50,000-token vocabulary
trained on it (Part B). The tokenizer uses only the standard library, `regex`, `numpy` and `tqdm`.

## Layout

| Path | Contents |
|---|---|
| `sources.json` | Every source: input path, format, genre, URL, licence, collection date |
| `urdu_corpus/scrape.py` | Polite, resumable news scraper (robots.txt, crawl log, manifest, raw HTML samples) |
| `urdu_corpus/wiki_to_jsonl.py` | Urdu Wikipedia parquet shards to JSONL |
| `urdu_corpus/normalize.py` | `normalize(text)`: Urdu Unicode normalisation |
| `urdu_corpus/clean_pipeline.py` | Extract, normalise, language filter, dedup, boilerplate removal, 98/1/1 split |
| `urdu_corpus/data_card.py` | Renders `corpus/DATA_CARD.md` from `sources.json` and `corpus/stats.json` |
| `urdu_corpus/check_corpus.py` | Streaming sanity checks of the split files |
| `urdu_bpe/pretokenize.py` | `<\|endoftext\|>` handling and the Urdu pre-tokenisation regex |
| `urdu_bpe/bpe_reference.py` | Reference trainer: recounts every pair after every merge |
| `urdu_bpe/bpe.py` | `BPETokenizer`: fast trainer, encode (with word cache), decode, save, load |
| `urdu_bpe/make_sample.py` | 1 MB sample of whole documents for the trainer comparison |
| `urdu_bpe/train_tokenizer.py` | Full training run; writes `artifacts/tokenizer.json` |
| `urdu_bpe/encode_corpus.py` | Streams `train.txt` / `val.txt` into `train.bin` / `val.bin` (uint16) and `encode_stats.json` |
| `urdu_bpe/verify_bins.py` | Decodes a `.bin` and compares it byte for byte with its `.txt` |
| `urdu_bpe/analysis.py` | Part C: tokens per word vs GPT-2 and o200k_base, hand-picked inputs, worst words |
| `report/` | `hand_inputs.json` (the seven inputs), analysis outputs, `report.pdf` |
| `tests/` | Normalisation, pipeline (synthetic sources), trainer equivalence, round trip |
| `raw/` | Inputs: `scraped/<site>/`, `urdu-plain-text-corpus.gz`, `wiki/*.parquet`, `urwiki.jsonl` |
| `corpus/` | `train.txt`, `val.txt`, `test.txt`, `stats.json`, `DATA_CARD.md` |
| `data/`, `artifacts/` | `sample_1mb.txt`; `tokenizer.json`, `train.bin`, `val.bin`, `encode_stats.json` |

## Setup

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Run every command from the repository root.

## Part A: corpus

```
python -m urdu_corpus.scrape --site jang --contact <your e-mail>
python -m urdu_corpus.scrape --site independent --contact <your e-mail>
python -m urdu_corpus.scrape --site express_live --contact <your e-mail>
python -m urdu_corpus.wiki_to_jsonl --src raw/wiki
python -m urdu_corpus.clean_pipeline
python -m urdu_corpus.data_card
python -m urdu_corpus.check_corpus
```

Downloads: UFAL Urdu Monolingual Corpus plain text to `raw/urdu-plain-text-corpus.gz`
(https://lindat.mff.cuni.cz/repository/xmlui/handle/11858/00-097C-0000-0023-65A9-5); Wikipedia
shards from https://huggingface.co/datasets/wikimedia/wikipedia/tree/main/20231101.ur to `raw/wiki/`.
The scraper resumes from `crawl_log.csv`, so it can be stopped and restarted.

## Part B: tokenizer

```
python -m urdu_bpe.make_sample
python -m unittest -v
python -m urdu_bpe.train_tokenizer
python -m urdu_bpe.encode_corpus
python -m urdu_bpe.verify_bins --split val
```

`encode_corpus` writes `artifacts/train.bin`, `artifacts/val.bin` and `artifacts/encode_stats.json`. `verify_bins` decodes
the `.bin` back and checks it equals the text exactly (run it on `--split train` too if time allows).

## Part C: analysis

```
pip install tiktoken matplotlib
python -m urdu_bpe.analysis
```

Needs internet on first run (tiktoken downloads the `gpt2` and `o200k_base` vocabularies). Reads `corpus/test.txt` and
`report/hand_inputs.json`; writes `q2_test.csv`, `q2_hand.csv`, `q2_hand.png`, `q3_candidates.json` and
`q3_worst_words.csv` to `report/`. `tiktoken` is used for comparison only, never in the tokenizer.

`BPE_EQ_MERGES=<n>` sets how many merges the fast and reference trainers are compared on (default 1000).

### Final report and submission

The completed analysis uses the entire 11.08 MB `test.txt` split (3,093 documents). On that split, the tokenizer
averages **1.170 tokens/word**, compared with **5.692** for GPT-2 and **1.545** for `o200k_base`. The hand-picked
tests surface three weak spots: Roman Urdu in Latin script, raw Urdu with diacritics, and Urdu-English code-switching.
The measured comparisons and examples are in `report/report.pdf`; detailed machine-readable results are alongside it.

`report/report.pdf` includes **Member A's Q1 corpus section**, the full Q2 comparison, and three Q3 failure cases.
Rebuild it after analysis with:

```
python report/build_report.py
```

The source register still has TODO entries for publisher terms and collection dates, and raw crawl-evidence directories
are not included in this workspace. Those gaps are disclosed in the report and should be resolved before redistribution.
The final ZIP contains the cleaned corpus splits, tokenizer, encoded binaries, source files, and report outputs; it
does not contain raw source downloads.

On the GitHub `adeenah` branch, `artifacts/train.bin` and `artifacts/val.bin` are stored with Git LFS because they
exceed GitHub's regular per-file limit. Install Git LFS before cloning/pulling to retrieve their contents. The large
final ZIP and source corpus text files are not tracked in that branch.

## Results

| | |
|---|---|
| Corpus | 1,094.72 MB cleaned, 304,040 documents, 132,963,869 words, 908,493 unique words (`corpus/DATA_CARD.md`) |
| Self-collected | 51.02 MB raw / 50.36 MB cleaned from jang.com.pk, independenturdu.com and express.pk |
| Training | 49,743 merges (IDs 257-49,999) in 186.3 s wall clock: 87.3 s counting 1,039,308 distinct words, 99.0 s merging |
| Machine | Intel Core i5-1145G7 (4 cores, 8 threads), 15.7 GB RAM, Windows 11, Python 3.14.6, single process |
| Check | fast/reference trainers learn the same first 3,000 merges on `data/sample_1mb.txt` (869 s); train: 162,137,642 uint16 tokens (6.69 bytes/token), val: 1,623,470 (6.714 bytes/token); both binaries decode byte-for-byte to their source text |

## Assignment checklist (up to encoding)

| Requirement | Where |
|---|---|
| >= 500 MB cleaned, 3+ sources, 2+ genres | `corpus/DATA_CARD.md` sections 1-2 |
| >= 50 MB self-collected, with evidence | `urdu_corpus/scrape.py`; evidence in `raw/scraped/<site>/` |
| Licence of every source | `sources.json`, data card section 1 |
| Extract, normalise, filter, dedup, split 98/1/1 by document with seed, `<\|endoftext\|>` | `urdu_corpus/clean_pipeline.py`, `urdu_corpus/normalize.py` |
| One-page data card | `corpus/DATA_CARD.md` (generated) |
| Byte vocab 0-255, `<\|endoftext\|>` = 256, merges 257-49,999, tie-break on bytes, lossless | `urdu_bpe/bpe.py`, `tests/test_roundtrip.py` |
| Urdu pre-tokenisation regex | `urdu_bpe/pretokenize.py` |
| Reference version, sanity check and 1 MB sample | `urdu_bpe/bpe_reference.py`, `tests/test_equivalence.py` |
| Fast version with the three optimisations, same merges as reference | `urdu_bpe/bpe.py`, `tests/test_equivalence.py` |
| Wall-clock time and machine | `artifacts/tokenizer.json` (`train_info`), Results above |
| `train.bin`, `val.bin` (uint16) | `urdu_bpe/encode_corpus.py`, `urdu_bpe/verify_bins.py` |

Pre-tokenisation (`urdu_bpe/pretokenize.py`) keeps GPT-2's structure but puts combining marks
(`\p{M}`) and ZWNJ/ZWJ inside the word class, so a word with diacritics or ZWNJ stays one piece;
a leading space belongs to the following word, and runs of newlines form one piece.
