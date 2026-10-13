## Merges 1-50

| # | token | type | # | token | type |
|---|---|---|---|---|---|
| 1 | ␣\xd8 | not valid UTF-8 | 26 | گ | char rebuilt |
| 2 | ی | char rebuilt | 27 | ب | char rebuilt |
| 3 | ا | char rebuilt | 28 | ␣ت | valid |
| 4 | ␣\xd9 | not valid UTF-8 | 29 | ␣ن | valid |
| 5 | ک | char rebuilt | 30 | ␣کی | whole word |
| 6 | ر | char rebuilt | 31 | ۔ | char rebuilt |
| 7 | ہ | char rebuilt | 32 | ور | valid |
| 8 | و | char rebuilt | 33 | ␣پ | valid |
| 9 | ے | char rebuilt | 34 | ␣کے | whole word |
| 10 | ␣ک | valid | 35 | ان | whole word |
| 11 | ن | char rebuilt | 36 | ␣ج | valid |
| 12 | ل | char rebuilt | 37 | ␣میں | whole word |
| 13 | ␣ا | valid | 38 | ␣د | valid |
| 14 | ا\xd8 | not valid UTF-8 | 39 | ار | valid |
| 15 | ں | char rebuilt | 40 | ␣ہے | whole word |
| 16 | م | char rebuilt | 41 | ع | char rebuilt |
| 17 | ␣م | valid | 42 | ␣و | valid |
| 18 | ت | char rebuilt | 43 | ␣۔ | valid |
| 19 | ␣ہ | valid | 44 | ق | char rebuilt |
| 20 | س | char rebuilt | 45 | ف | char rebuilt |
| 21 | ھ | char rebuilt | 46 | ٹ | char rebuilt |
| 22 | یں | valid | 47 | چ | char rebuilt |
| 23 | ␣ب | valid | 48 | ج | char rebuilt |
| 24 | د | char rebuilt | 49 | ␣ل | valid |
| 25 | ␣س | valid | 50 | پ | char rebuilt |

## Every 5,000th merge

| merge | pair | token | bytes | type |
|---|---|---|---|---|
| 5000 | ␣نشان + دہی | ␣نشاندہی | 15 | valid |
| 10000 | ی + تی | یتی | 6 | valid |
| 15000 | ␣ناپسند + یدہ | ␣ناپسندیدہ | 19 | valid |
| 20000 | بال + ہ | بالہ | 8 | valid |
| 25000 | ␣مارکیٹ + وں | ␣مارکیٹوں | 17 | valid |
| 30000 | جعفر + آباد | جعفرآباد | 16 | valid |
| 35000 | ␣رگ + ھو | ␣رگھو | 9 | valid |
| 40000 | ␣ہڑتال + یں | ␣ہڑتالیں | 15 | valid |
| 45000 | راجی + ش | راجیش | 10 | valid |

## Merges 1-50 by type

- two-byte character rebuilt (25): 2 ی, 3 ا, 5 ک, 6 ر, 7 ہ, 8 و, 9 ے, 11 ن, 12 ل, 15 ں, 16 م, 18 ت, 20 س, 21 ھ, 24 د, 26 گ, 27 ب, 31 ۔, 41 ع, 44 ق, 45 ف, 46 ٹ, 47 چ, 48 ج, 50 پ
- not valid UTF-8 (3): 1 ␣\xd8, 4 ␣\xd9, 14 ا\xd8

## First whole words (>= 2 letters, >= 100 occurrences in val.txt)

| merge | token | count in val.txt |
|---|---|---|
| 30 | ␣کی | 34217 |
| 34 | ␣کے | 44137 |
| 35 | ان | 6720 |
| 37 | ␣میں | 39845 |
| 40 | ␣ہے | 32809 |

## 20 longest tokens

| rank | merge | token | bytes | chars |
|---|---|---|---|---|
| 1 | 14863 | ␣انسائیکلوپیڈیا | 29 | 15 |
| 2 | 29403 | ␣انٹرکانٹینینٹل | 29 | 15 |
| 3 | 44404 | انسائیکلوپیڈیا | 28 | 14 |
| 4 | 48305 | ہاہاہاہاہاہاہا | 28 | 14 |
| 5 | 9733 | ␣انانکارپوریٹڈ | 27 | 14 |
| 6 | 15051 | ␣خیبرپختونخوا | 25 | 13 |
| 7 | 27589 | ␣امیرالمومنین | 25 | 13 |
| 8 | 29228 | ␣امیرالمؤمنین | 25 | 13 |
| 9 | 35767 | ␣دارالحکومتوں | 25 | 13 |
| 10 | 37298 | ␣طالبانائزیشن | 25 | 13 |
| 11 | 40788 | ␣گوانتاناموبے | 25 | 13 |
| 12 | 46675 | ␣ٹرانسپورٹیشن | 25 | 13 |
| 13 | 47259 | ␣انفرااسٹرکچر | 25 | 13 |
| 14 | 48191 | ␣موٹرسائیکلوں | 25 | 13 |
| 15 | 48405 | ␣ہاہاہاہاہاہا | 25 | 13 |
| 16 | 48694 | ␣چیکوسلوواکیا | 25 | 13 |
| 17 | 49086 | ␣آسٹریلیائیوں | 25 | 13 |
| 18 | 36757 | ہاہاہاہاہاہا | 24 | 12 |
| 19 | 39669 | محمدعبیداللہ | 24 | 12 |
| 20 | 42442 | نویدظفرکیانی | 24 | 12 |
