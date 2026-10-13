## Tokens per word on the three inputs

| input | words | ours tokens | ours | ours + normalize | o200k_base |
|---|---|---|---|---|---|
| diacritics (harakat) | 5 | 20 | 4.00 | 1.00 | 3.00 |
| Roman Urdu | 10 | 26 | 2.60 | 2.60 | 2.00 |
| Arabic code points and Urdu digits | 11 | 33 | 3.00 | 1.00 | 1.82 |

## Segmentation (tokens separated by ·, space shown as ␣)

**diacritics (harakat)**

- ours: ا · \xd9 · \x8f · رد · \xd9 · \x8f · و · ␣ہ · \xd9 · \x8e · ماری · ␣ق · \xd9 · \x8e · ومی · ␣ز · \xd9 · \x8e · بان · ␣ہے
- ours + normalize: اردو · ␣ہماری · ␣قومی · ␣زبان · ␣ہے

**Roman Urdu**

- ours: M · ain · ␣the · ek · ␣h · oon · , · ␣sh · uk · ri · ya · . · ␣K · al · ␣h · um · ␣b · aza · ar · ␣j · a · ␣ra · he · ␣h · ain · .
- ours + normalize: M · ain · ␣the · ek · ␣h · oon · , · ␣sh · uk · ri · ya · . · ␣K · al · ␣h · um · ␣b · aza · ar · ␣j · a · ␣ra · he · ␣h · ain · .

**Arabic code points and Urdu digits**

- ours: پا · \xd9 · \x83 · ستان · ␣\xd9 · \x83 · \xd9 · \x8a · ␣ح · \xd9 · \x83 · ومت · ␣نے · ␣\xdb · \xb1 · \xdb · \xb4 · ␣اگست · ␣\xd9 · \x83 · و · ␣چھٹ · \xd9 · \x8a · ␣\xd9 · \x83 · ا · ␣اعلان · ␣\xd9 · \x83 · \xd9 · \x8a · ا
- ours + normalize: پاکستان · ␣کی · ␣حکومت · ␣نے · ␣14 · ␣اگست · ␣کو · ␣چھٹی · ␣کا · ␣اعلان · ␣کیا
