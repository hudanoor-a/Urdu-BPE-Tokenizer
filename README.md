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
| `urdu_bpe/encode_corpus.py` | Placeholder: `train.bin` / `val.bin` (uint16) |
| `tests/` | Normalisation, pipeline (synthetic sources), trainer equivalence, round trip |
| `raw/` | Inputs: `scraped/<site>/`, `urdu-plain-text-corpus.gz`, `wiki/*.parquet`, `urwiki.jsonl` |
| `corpus/` | `train.txt`, `val.txt`, `test.txt`, `stats.json`, `DATA_CARD.md` |
| `data/`, `artifacts/` | `sample_1mb.txt`; `tokenizer.json` (and later `train.bin`, `val.bin`) |

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

## Part B: rebuild the tokenizer from train.txt

`corpus/train.txt` is not in git (1.08 GB). Produce it with Part A, or copy it into `corpus/`. Then run
these PowerShell commands from the repository root, in order (after Setup):

```powershell
# 1. Confirm the input is the corpus the published tokenizer was trained on
(Get-FileHash corpus/train.txt -Algorithm SHA256).Hash
(Get-Item corpus/train.txt).Length
python -m urdu_corpus.check_corpus

# 2. Check the trainers on a 1 MB sample (fast vs reference, sanity check, round trip); about 6 minutes
python -m urdu_bpe.make_sample --train corpus/train.txt --out data/sample_1mb.txt --min-bytes 1000000 --seed 42
python -m unittest -v

# 3. Train to 50,000 tokens; about 3 minutes
python -m urdu_bpe.train_tokenizer --train corpus/train.txt --vocab-size 50000 --out artifacts/tokenizer.json

# 4. Confirm the rebuilt merges match the published ones
python -c "import hashlib, json; m = json.load(open('artifacts/tokenizer.json', encoding='utf-8'))['merges']; print(len(m), hashlib.sha256(json.dumps(m).encode()).hexdigest())"
```

Expected output:

| Step | Output |
|---|---|
| 1 | `17BFA9CF3652730A7F51B38FC763D37103DFE34BEE46E055B873D6F5D1BE221F`, `1077388411`, then `OVERALL: PASS (0 failed checks)` |
| 2 | `wrote data\sample_1mb.txt: 1,002,531 bytes, 152 documents, from offset 686,579,303`, then `Ran 19 tests ... OK` |
| 3 | `distinct_words: 1,039,308`, `word_occurrences: 149,099,878`, `merges learned: 49,743 (vocab size 50,000)`, `wall-clock time: ...`, `saved artifacts\tokenizer.json` |
| 4 | `49743 d83da5b95da248a9d90071b0979e401e5cf4e2765f5de77ab5ceeb7f2d6f131d` |

Training is deterministic, so step 4 prints the same hash on any machine; only the timings stored in
`train_info` change. `$env:BPE_EQ_MERGES = "3000"` before step 2 compares more merges (default 1000).

Encoding `train.txt` and `val.txt` to `train.bin` / `val.bin` (`python -m urdu_bpe.encode_corpus`) is
still a placeholder.

## Part C: analysis

```
python -m analysis.q1_merges
python -m analysis.q2_compare
python -m analysis.q3_failures
```

Each writes a Markdown table file to `analysis/output/`; the report is `analysis/REPORT.md`.
`tiktoken` is used only here, for the GPT-2 and o200k_base comparison.

## Results

| | |
|---|---|
| Corpus | 1,094.72 MB cleaned, 304,040 documents, 132,963,869 words, 908,493 unique words (`corpus/DATA_CARD.md`) |
| Self-collected | 51.02 MB raw / 50.36 MB cleaned from jang.com.pk, independenturdu.com and express.pk |
| Training | 49,743 merges (IDs 257-49,999) in 186.3 s wall clock: 87.3 s counting 1,039,308 distinct words, 99.0 s merging |
| Machine | Intel Core i5-1145G7 (4 cores, 8 threads), 15.7 GB RAM, Windows 11, Python 3.14.6, single process |
| Check | fast and reference trainers learn the same first 3,000 merges, in order, on `data/sample_1mb.txt` (869 s); `val.txt` encodes to 1,551,320 tokens (6.98 bytes/token) and decodes back exactly |

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
| `train.bin`, `val.bin` (uint16) | `urdu_bpe/encode_corpus.py` (placeholder) |

Pre-tokenisation (`urdu_bpe/pretokenize.py`) keeps GPT-2's structure but puts combining marks
(`\p{M}`) and ZWNJ/ZWJ inside the word class, so a word with diacritics or ZWNJ stays one piece;
a leading space belongs to the following word, and runs of newlines form one piece.
