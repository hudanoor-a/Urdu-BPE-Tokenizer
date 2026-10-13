# Part C: Analysis of the Urdu BPE tokenizer

Tokenizer: byte-level BPE, 50,000 tokens (256 bytes, `<|endoftext|>` = 256, 49,743 merges), trained on
`corpus/train.txt` (1,077 MB). Tables are produced by `python -m analysis.q1_merges`, `q2_compare` and
`q3_failures`. In token strings, `␣` is a space and `\xNN` is a byte that is not valid UTF-8 on its own.

## 1. What did the merges learn?

**Merges 1-50** (type: *char* = two bytes rebuilt into one character; *invalid* = not valid UTF-8 on its
own; *word* = whole word, i.e. at least two letters and at least 100 occurrences as a complete word in `val.txt`)

| # | token | type | # | token | type |
|---|---|---|---|---|---|
| 1 | ␣\xd8 | invalid | 26 | گ | char |
| 2 | ی | char | 27 | ب | char |
| 3 | ا | char | 28 | ␣ت | subword |
| 4 | ␣\xd9 | invalid | 29 | ␣ن | subword |
| 5 | ک | char | 30 | ␣کی | **word** |
| 6 | ر | char | 31 | ۔ | char |
| 7 | ہ | char | 32 | ور | subword |
| 8 | و | char | 33 | ␣پ | subword |
| 9 | ے | char | 34 | ␣کے | word |
| 10 | ␣ک | subword | 35 | ان | word |
| 11 | ن | char | 36 | ␣ج | subword |
| 12 | ل | char | 37 | ␣میں | word |
| 13 | ␣ا | subword | 38 | ␣د | subword |
| 14 | ا\xd8 | invalid | 39 | ار | subword |
| 15 | ں | char | 40 | ␣ہے | word |
| 16 | م | char | 41 | ع | char |
| 17 | ␣م | subword | 42 | ␣و | subword |
| 18 | ت | char | 43 | ␣۔ | subword |
| 19 | ␣ہ | subword | 44 | ق | char |
| 20 | س | char | 45 | ف | char |
| 21 | ھ | char | 46 | ٹ | char |
| 22 | یں | subword | 47 | چ | char |
| 23 | ␣ب | subword | 48 | ج | char |
| 24 | د | char | 49 | ␣ل | subword |
| 25 | ␣س | subword | 50 | پ | char |

**Every 5,000th merge**

| merge | pair | token | merge | pair | token |
|---|---|---|---|---|---|
| 5,000 | ␣نشان + دہی | ␣نشاندہی | 30,000 | جعفر + آباد | جعفرآباد |
| 10,000 | ی + تی | یتی | 35,000 | ␣رگ + ھو | ␣رگھو |
| 15,000 | ␣ناپسند + یدہ | ␣ناپسندیدہ | 40,000 | ␣ہڑتال + یں | ␣ہڑتالیں |
| 20,000 | بال + ہ | بالہ | 45,000 | راجی + ش | راجیش |
| 25,000 | ␣مارکیٹ + وں | ␣مارکیٹوں | | | |

**20 longest tokens** (bytes / characters)

| merge | token | size | merge | token | size |
|---|---|---|---|---|---|
| 14,863 | ␣انسائیکلوپیڈیا | 29 / 15 | 37,298 | ␣طالبانائزیشن | 25 / 13 |
| 29,403 | ␣انٹرکانٹینینٹل | 29 / 15 | 40,788 | ␣گوانتاناموبے | 25 / 13 |
| 44,404 | انسائیکلوپیڈیا | 28 / 14 | 46,675 | ␣ٹرانسپورٹیشن | 25 / 13 |
| 48,305 | ہاہاہاہاہاہاہا | 28 / 14 | 47,259 | ␣انفرااسٹرکچر | 25 / 13 |
| 9,733 | ␣انانکارپوریٹڈ | 27 / 14 | 48,191 | ␣موٹرسائیکلوں | 25 / 13 |
| 15,051 | ␣خیبرپختونخوا | 25 / 13 | 48,405 | ␣ہاہاہاہاہاہا | 25 / 13 |
| 27,589 | ␣امیرالمومنین | 25 / 13 | 48,694 | ␣چیکوسلوواکیا | 25 / 13 |
| 29,228 | ␣امیرالمؤمنین | 25 / 13 | 49,086 | ␣آسٹریلیائیوں | 25 / 13 |
| 35,767 | ␣دارالحکومتوں | 25 / 13 | 36,757 | ہاہاہاہاہاہا | 24 / 12 |
| 39,669 | محمدعبیداللہ | 24 / 12 | 42,442 | نویدظفرکیانی | 24 / 12 |

Urdu letters are two bytes in UTF-8 (lead byte 0xD8-0xDB), so the very first merges glue a space to the lead
byte of a word-initial letter (1 `␣\xd8`, 4 `␣\xd9`, and 14 `ا\xd8`): the three early tokens that are not
valid UTF-8 on their own. Half of merges 1-50 (25 of them) rebuild a two-byte character, in frequency
order ی ا ک ر ہ و ے, 24 letters plus the full stop ۔ (merge 31). The first whole word appears at merge 30
(`␣کی`, "of"), followed by `␣کے`, `␣میں` and `␣ہے`, the most frequent function words. Later merges add
inflected content words, place and personal names, and long loanwords. The longest tokens also show corpus
quirks: laughter (ہاہاہا) and names written without spaces (محمدعبیداللہ).

## 2. How does it compare with existing tokenizers?

Tokens per whitespace-separated word (lower is better). `ours + normalize` applies the corpus `normalize()`
first, as was done for the training text. GPT-2 is `gpt2`, the modern multilingual tokenizer is `o200k_base`
(tiktoken 0.14.0); `test.txt` is the held-out split without `<|endoftext|>` lines.

| input | words | ours | ours + normalize | gpt2 | o200k_base |
|---|---|---|---|---|---|
| test.txt | 1,410,766 | **1.12** | 1.12 | 5.65 | 1.54 |
| news | 32 | **1.03** | 1.03 | 5.94 | 1.38 |
| poetry (Ghalib, Iqbal) | 38 | **1.08** | 1.08 | 5.74 | 1.61 |
| Urdu with English words | 21 | 1.67 | 1.67 | 3.57 | **1.10** |
| Roman Urdu | 17 | 2.71 | 2.71 | 2.24 | **2.00** |
| numbers and dates | 23 | **1.61** | 1.61 | 5.26 | 2.09 |
| text with diacritics | 9 | 6.89 | **1.22** | 9.00 | 4.44 |
| personal names | 17 | **1.24** | 1.24 | 6.82 | 2.18 |

On `test.txt` our tokenizer needs 1,583,546 tokens (6.96 bytes per token), o200k_base 1.37 times as many
and GPT-2 5.03 times as many; GPT-2 averages 1.38 bytes per token, less than one Urdu letter. With a vocabulary
four times smaller than o200k_base, ours wins on every Urdu-script input (news, poetry, names, numbers),
because all of its merges are spent on Urdu. It loses on Latin-script text (Roman Urdu, English words), which
the cleaning step largely filtered out, and on diacritics unless the input is normalised first.

## 3. Three inputs the tokenizer handles badly

| input | words | ours | ours + normalize | o200k_base |
|---|---|---|---|---|
| اُردُو ہَماری قَومی زَبان ہے | 5 | 4.00 | 1.00 | 3.00 |
| Main theek hoon, shukriya. Kal hum bazaar ja rahe hain. | 10 | 2.60 | 2.60 | 2.00 |
| پاكستان كي حكومت نے ۱۴ اگست كو چھٹي كا اعلان كيا (Arabic kaf and yeh, Urdu digits) | 11 | 3.00 | 1.00 | 1.82 |

Segmentation by our tokenizer (`·` separates tokens):

1. **Diacritics.** `ا · \xd9 · \x8f · رد · \xd9 · \x8f · و · ␣ہ · \xd9 · \x8e · ماری · …`
   `normalize()` removed harakat from the training text, so zabar and pesh (U+064E, U+064F) never occurred and
   not even their two bytes were merged; each mark costs two byte tokens and cuts the word around it. After
   normalisation the same sentence is one token per word.
2. **Roman Urdu.** `M · ain · ␣the · ek · ␣h · oon · , · ␣sh · uk · ri · ya · …`
   Lines with less than half Urdu-script letters were dropped during cleaning, so Latin script is rare in
   training and only frequent English fragments (`␣the`, `ain`) became tokens. Roman Urdu, common in
   informal writing, costs 2.6-2.7 tokens per word, more than GPT-2 (2.24 in section 2) and o200k_base.
3. **Unnormalised Arabic code points and Urdu digits.** `پا · \xd9 · \x83 · ستان · ␣\xd9 · \x83 · \xd9 · \x8a · … · ␣\xdb · \xb1 · \xdb · \xb4 · …`
   Text typed on an Arabic keyboard uses Arabic kaf/yeh (U+0643, U+064A), and Urdu digits ۱۴ (U+06F1, U+06F4)
   instead of ASCII. Normalisation mapped all of these away, so they have no merges and fall back to raw bytes:
   three times as many tokens as the normalised text. The tokenizer stays lossless, but any text fed to it must
   go through the same `normalize()` as the corpus.
