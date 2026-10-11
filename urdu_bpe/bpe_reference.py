"""Reference BPE trainer: every word occurrence kept separately, all pairs recounted after every merge.

Too slow for the full corpus; it exists to check the fast trainer in bpe.py on small inputs.
Only the pre-tokenisation is shared with bpe.py; counting, tie-breaking and merging are separate.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import regex
from tqdm import tqdm

from .pretokenize import FIRST_MERGE_ID, SPLIT_PATTERN, iter_file_segments, iter_text_segments, list_words


def reference_merges(words: list[bytes], num_merges: int, verbose: bool = False) -> list[tuple[int, int]]:
    """Ordered merged pairs; merge k creates ID 257 + k."""
    vocab = {i: bytes([i]) for i in range(256)}
    seqs = [list(w) for w in words]
    merges: list[tuple[int, int]] = []
    for k in tqdm(range(num_merges), desc="merges (reference)", disable=not verbose):
        counts: Counter[tuple[int, int]] = Counter()
        for s in seqs:
            counts.update(zip(s, s[1:]))
        if not counts:
            break
        best = max(counts, key=lambda p: (counts[p], vocab[p[0]], vocab[p[1]]))
        new_id = FIRST_MERGE_ID + k
        vocab[new_id] = vocab[best[0]] + vocab[best[1]]
        merges.append(best)
        seqs = [_replace(s, best, new_id) for s in seqs]
    return merges


def _replace(seq: list[int], pair: tuple[int, int], new_id: int) -> list[int]:
    out, i = [], 0
    while i < len(seq):
        if seq[i] == pair[0] and i + 1 < len(seq) and seq[i + 1] == pair[1]:
            out.append(new_id)
            i += 2
        else:
            out.append(seq[i])
            i += 1
    return out


def train_reference(path: Path, num_merges: int, verbose: bool = False) -> list[tuple[int, int]]:
    return reference_merges(list_words(iter_file_segments(path), regex.compile(SPLIT_PATTERN)), num_merges, verbose)


def train_reference_text(text: str, num_merges: int) -> list[tuple[int, int]]:
    return reference_merges(list_words(iter_text_segments(text), regex.compile(SPLIT_PATTERN)), num_merges)
