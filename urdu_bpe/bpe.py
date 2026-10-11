"""Byte-level BPE tokenizer.

Vocabulary: IDs 0-255 are the byte values, 256 is <|endoftext|> (never split, never merged) and
257 onwards are merges in the order they were learned.
"""

from __future__ import annotations

import heapq
import json
import time
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

import regex
from tqdm import tqdm

from .bpe_reference import reference_merges
from .pretokenize import (
    EOT_ID,
    EOT_TOKEN,
    FIRST_MERGE_ID,
    SPLIT_PATTERN,
    count_words,
    iter_file_segments,
    iter_text_segments,
    list_words,
)

Pair = tuple[int, int]


def merge_ids(ids: list[int], pair: Pair, new_id: int) -> list[int]:
    """Replace every non-overlapping occurrence of pair, left to right, with new_id."""
    a, b = pair
    out: list[int] = []
    i, n = 0, len(ids)
    while i < n:
        if i < n - 1 and ids[i] == a and ids[i + 1] == b:
            out.append(new_id)
            i += 2
        else:
            out.append(ids[i])
            i += 1
    return out


class BPETokenizer:
    def __init__(self, pattern: str = SPLIT_PATTERN) -> None:
        self.pattern = pattern
        self.compiled = regex.compile(pattern)
        self.merges: dict[Pair, int] = {}
        self.vocab: dict[int, bytes] = self._base_vocab()
        self.cache: dict[str, list[int]] = {}
        self.train_info: dict = {}

    @staticmethod
    def _base_vocab() -> dict[int, bytes]:
        vocab = {i: bytes([i]) for i in range(256)}
        vocab[EOT_ID] = EOT_TOKEN.encode("utf-8")
        return vocab

    def _add_merge(self, pair: Pair) -> int:
        new_id = FIRST_MERGE_ID + len(self.merges)
        self.merges[pair] = new_id
        self.vocab[new_id] = self.vocab[pair[0]] + self.vocab[pair[1]]
        return new_id

    def _rank(self, pair: Pair, count: int) -> tuple[int, bytes, bytes]:
        """Merge order: higher count first; ties go to the greater pair compared as (bytes, bytes)."""
        return count, self.vocab[pair[0]], self.vocab[pair[1]]

    # ------------------------------------------------------------------ training

    def train(self, path: Path, vocab_size: int, fast: bool = True, verbose: bool = False) -> None:
        """Learn vocab_size - 257 merges from a text file."""
        self._train(iter_file_segments(path, show_progress=verbose), vocab_size, fast, verbose)

    def train_text(self, text: str, vocab_size: int, fast: bool = True, verbose: bool = False) -> None:
        self._train(iter_text_segments(text), vocab_size, fast, verbose)

    def _train(self, segments: Iterable[str], vocab_size: int, fast: bool, verbose: bool) -> None:
        num_merges = vocab_size - FIRST_MERGE_ID
        if num_merges < 0:
            raise ValueError(f"vocab_size must be at least {FIRST_MERGE_ID}")
        self.merges, self.vocab, self.cache = {}, self._base_vocab(), {}
        if not fast:
            for pair in reference_merges(list_words(segments, self.compiled), num_merges, verbose):
                self._add_merge(pair)
            return
        start = time.perf_counter()
        word_counts = count_words(segments, self.compiled)
        counted = time.perf_counter()
        self._train_fast(word_counts, num_merges, verbose)
        self.train_info.update(
            distinct_words=len(word_counts),
            word_occurrences=sum(word_counts.values()),
            count_seconds=round(counted - start, 1),
            merge_seconds=round(time.perf_counter() - counted, 1),
        )

    def _train_fast(self, word_counts: Counter[bytes], num_merges: int, verbose: bool = False) -> None:
        """Merges from distinct words weighted by frequency, updating only the words that contain the pair.

        index maps each pair to the words that contained it when it appeared; entries can go stale
        and are skipped when merging. The heap holds (-count, pair) and is refreshed lazily: a new
        entry is pushed when a count rises, and an entry whose count has fallen is re-queued when it
        reaches the top.
        """
        words = [list(w) for w in word_counts]
        freqs = list(word_counts.values())
        pair_counts: dict[Pair, int] = {}
        index: dict[Pair, list[int]] = {}
        for i, (w, f) in enumerate(zip(words, freqs)):
            for p in zip(w, w[1:]):
                pair_counts[p] = pair_counts.get(p, 0) + f
                self._index_add(index, p, i)
        heap = [(-c, p) for p, c in pair_counts.items()]
        heapq.heapify(heap)

        for _ in tqdm(range(num_merges), desc="merges", disable=not verbose, mininterval=5):
            best = self._pop_best(heap, pair_counts)
            if best is None:
                break
            new_id = self._add_merge(best)
            delta: dict[Pair, int] = {}
            for i in set(index.pop(best, ())):
                old = words[i]
                new = merge_ids(old, best, new_id)
                if len(new) == len(old):
                    continue
                f = freqs[i]
                for p in zip(old, old[1:]):
                    delta[p] = delta.get(p, 0) - f
                for p in zip(new, new[1:]):
                    delta[p] = delta.get(p, 0) + f
                    if new_id in p:
                        self._index_add(index, p, i)
                words[i] = new
            pair_counts.pop(best, None)
            delta.pop(best, None)
            for p, d in delta.items():
                if not d:
                    continue
                c = pair_counts.get(p, 0) + d
                if c > 0:
                    pair_counts[p] = c
                    if d > 0:
                        heapq.heappush(heap, (-c, p))
                else:
                    pair_counts.pop(p, None)

    @staticmethod
    def _index_add(index: dict[Pair, list[int]], pair: Pair, word: int) -> None:
        words = index.setdefault(pair, [])
        if not words or words[-1] != word:
            words.append(word)

    def _pop_best(self, heap: list, pair_counts: dict[Pair, int]) -> Pair | None:
        while heap:
            neg, pair = heapq.heappop(heap)
            count = pair_counts.get(pair, 0)
            if count == -neg:
                break
            if count > 0:
                heapq.heappush(heap, (-count, pair))
        else:
            return None

        ties = {pair}
        while heap and heap[0][0] == neg:
            _, other = heapq.heappop(heap)
            count = pair_counts.get(other, 0)
            if count == -neg:
                ties.add(other)
            elif count > 0:
                heapq.heappush(heap, (-count, other))
        best = max(ties, key=lambda p: self._rank(p, -neg))
        for other in ties - {best}:
            heapq.heappush(heap, (neg, other))
        return best

    # ------------------------------------------------------------------ encode / decode

    def _encode_word(self, word: str) -> list[int]:
        ids = self.cache.get(word)
        if ids is None:
            ids = list(word.encode("utf-8", errors="surrogatepass"))
            while len(ids) > 1:
                pair = min(zip(ids, ids[1:]), key=lambda p: self.merges.get(p, float("inf")))
                if pair not in self.merges:
                    break
                ids = merge_ids(ids, pair, self.merges[pair])
            self.cache[word] = ids
        return ids

    def encode(self, text: str) -> list[int]:
        """Text to IDs; <|endoftext|> becomes 256 and every word goes through the encode cache."""
        out: list[int] = []
        for k, segment in enumerate(iter_text_segments(text)):
            if k:
                out.append(EOT_ID)
            for word in self.compiled.findall(segment):
                out.extend(self._encode_word(word))
        return out

    def decode(self, ids: Iterable[int]) -> str:
        """IDs to text. Exact for any output of encode(); other byte sequences that are not valid
        UTF-8 decode with U+FFFD."""
        data = b"".join(self.vocab[i] for i in ids)
        try:
            return data.decode("utf-8", errors="surrogatepass")
        except UnicodeDecodeError:
            return data.decode("utf-8", errors="replace")

    # ------------------------------------------------------------------ persistence

    def save(self, path: Path) -> None:
        """JSON with the pattern, special token and merges in order (merge i creates ID 257 + i)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "pattern": self.pattern,
            "special_tokens": {EOT_TOKEN: EOT_ID},
            "vocab_size": FIRST_MERGE_ID + len(self.merges),
            "merges": [list(pair) for pair in self.merges],
            "train_info": self.train_info,
        }
        path.write_text(json.dumps(data, ensure_ascii=True), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> BPETokenizer:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        tok = cls(data["pattern"])
        for a, b in data["merges"]:
            tok._add_merge((a, b))
        tok.train_info = data.get("train_info", {})
        return tok
