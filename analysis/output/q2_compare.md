## Tokens per word

| input | words | ours | ours + normalize | gpt2 | o200k_base |
|---|---|---|---|---|---|
| test.txt | 1,410,766 | 1.12 | 1.12 | 5.65 | 1.54 |
| news | 32 | 1.03 | 1.03 | 5.94 | 1.38 |
| poetry | 38 | 1.08 | 1.08 | 5.74 | 1.61 |
| Urdu + English | 21 | 1.67 | 1.67 | 3.57 | 1.10 |
| Roman Urdu | 17 | 2.71 | 2.71 | 2.24 | 2.00 |
| numbers and dates | 23 | 1.61 | 1.61 | 5.26 | 2.09 |
| diacritics | 9 | 6.89 | 1.22 | 9.00 | 4.44 |
| personal names | 17 | 1.24 | 1.24 | 6.82 | 2.18 |

## test.txt totals

| tokenizer | tokens | bytes per token | tokens vs ours |
|---|---|---|---|
| ours | 1,583,546 | 6.96 | 1.00x |
| ours + normalize | 1,583,545 | 6.96 | 1.00x |
| gpt2 | 7,964,075 | 1.38 | 5.03x |
| o200k_base | 2,174,620 | 5.07 | 1.37x |
