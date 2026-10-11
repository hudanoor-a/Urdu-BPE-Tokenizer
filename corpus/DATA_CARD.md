# DATA CARD: Urdu corpus

## 1. Sources

| Source | Genre | URL | Licence / terms | Collected | Self-collected | Raw MB | Cleaned MB | Docs |
|---|---|---|---|---|---|---|---|---|
| jang | news | https://jang.com.pk | Copyright Daily Jang, all rights reserved (site footer); robots.txt obeyed; course-internal use, not redistributed | TODO | yes | 25.92 | 25.90 | 12,287 |
| independent_urdu | news | https://www.independenturdu.com | TODO: publisher terms of use; robots.txt obeyed; course-internal use, not redistributed | TODO | yes | 24.55 | 23.93 | 3,709 |
| express_live | news | https://www.express.pk/live-blog | TODO: publisher terms of use; robots.txt obeyed; course-internal use, not redistributed | TODO | yes | 0.54 | 0.53 | 7 |
| ufal_urdu_mono | mixed (news, religion, blogs, literature, science, education) | https://lindat.mff.cuni.cz/repository/xmlui/handle/11858/00-097C-0000-0023-65A9-5 | CC BY-NC-SA 3.0 (Jawaid, Kamran and Bojar, 2014) | 2026-10-10 | no | 717.30 | 715.75 | 109,292 |
| urdu_wikipedia | encyclopedia | https://huggingface.co/datasets/wikimedia/wikipedia (20231101.ur) | CC BY-SA 3.0 and GFDL | 2026-10-11 | no | 377.12 | 328.61 | 178,745 |

Self-collected by scraping: **51.02 MB raw, 50.36 MB cleaned** (requirement: 50 MB). Evidence: `raw/scraped/<site>/crawl_log.csv`, `manifest.csv`, dated `robots_*.txt` and `raw_samples/`.

## 2. Corpus totals

| Split | Docs | MB | Words |
|---|---|---|---|
| train.txt | 297,973 | 1,072.92 | 130,316,268 |
| val.txt | 2,974 | 10.78 | 1,308,174 |
| test.txt | 3,093 | 11.01 | 1,339,427 |
| **total** | 304,040 | 1,094.72 | 132,963,869 |

Unique words (regex `\w+`): **908,493**. Split 98/1/1 by document (seed 42), `<|endoftext|>` after each document. MB = 10^6 bytes of UTF-8 text.

## 3. Cleaning steps

| Step | What it does | MB before | MB after | Removed |
|---|---|---|---|---|
| 1 Extract | URLs and e-mails removed (HTML was reduced to article text by trafilatura at scrape time) | 1,145.44 | 1,145.25 | 0.0% |
| 2 Normalise | `normalize()`, section 4 | 1,145.25 | 1,140.43 | 0.4% |
| 3 Language filter | drop lines with < 50% Urdu-script letters, then docs < 100 chars | 1,140.43 | 1,131.94 | 0.7% |
| 4a Exact dedup | 1,897 duplicate documents (MD5 of cleaned text) | 1,131.94 | 1,131.34 | 0.1% |
| 4b Boilerplate | lines <= 150 chars found in >= 50 docs | 1,131.34 | 1,094.72 | 3.2% |

Documents: 325,452 read, 4,136 too short or not Urdu, 1,897 duplicates, 15,379 too short after boilerplate removal, 304,040 kept.

## 4. Normalisation decisions

- NFKC first (folds presentation forms and ligatures). Arabic yeh U+064A and alef maksura U+0649 to U+06CC; Arabic kaf U+0643 and swash kaf U+06AA to U+06A9; Arabic heh U+0647 to gol heh U+06C1 (do-chashmi heh U+06BE kept apart); teh marbuta U+0629 to U+06C3.
- Tatweel and harakat U+064B-U+0652 removed: they are used inconsistently and would split one word into several spellings. Superscript alef U+0670 and honorific signs U+0610-U+0615 are kept as part of the spelling.
- Digits: Arabic-Indic and Extended Arabic-Indic digits mapped to ASCII 0-9.
- ZWNJ U+200C: **remove**. Only urdu_wikipedia (4,560) contained ZWNJ, so its use is inconsistent across sources; keeping it would give one word two byte sequences and two sets of tokens.
- ZWJ, direction marks, bidi controls, BOM, soft hyphen and control characters removed; runs of spaces and non-breaking spaces collapsed to one space; line breaks unified to LF; empty lines dropped.

## 5. Known gaps and biases

- Genre shares by cleaned bytes: mixed (news, religion, blogs, literature, science, education) 65.4%; encyclopedia 30.0%; news 4.6%. The mixed-domain UFAL corpus dominates and its domains are unlabelled.
- Time skew: UFAL was released in 2014 and Wikipedia is the 2023-11-01 snapshot; only the scraped news covers recent events.
- UFAL is one sentence per line; every 50 lines form a pseudo-document, so its document boundaries are artificial.
- Formal written Urdu only: social media, chat, Roman Urdu and poetry are nearly absent; English-heavy lines are filtered out.
- Deduplication is exact only: near-duplicate news stories and templated Wikipedia stubs remain.
