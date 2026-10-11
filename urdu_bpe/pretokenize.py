"""Special token handling and regex pre-tokenisation shared by both trainers and the encoder."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Iterator
from pathlib import Path

import regex
from tqdm import tqdm

EOT_TOKEN = "<|endoftext|>"
EOT_ID = 256
FIRST_MERGE_ID = 257
READ_CHARS = 1 << 24

# GPT-2's layout, changed so Urdu words stay whole:
#   's 't ...    English contractions, as in GPT-2.
#   words        optional leading space, then letters (\p{L}), combining marks (\p{M}: zer, zabar,
#                pesh, superscript alef, ...) and ZWNJ/ZWJ. GPT-2 uses \p{L}+ and splits at all three.
#   numbers      optional leading space, then digits (\p{N} covers ASCII and Urdu digits).
#   symbols      optional leading space, then anything that is not space, letter, mark, digit or
#                ZWNJ/ZWJ: Urdu and Latin punctuation, emoji.
#   line breaks  \s*[\r\n]+ keeps a run of newlines (and \r\n) together.
#   spaces       as in GPT-2: a run of spaces leaves its last space to the next word.
# Every character matches a branch, so the pieces always concatenate back to the input.
SPLIT_PATTERN = (
    r"""'(?:s|t|re|ve|m|ll|d)"""
    r"""| ?[\p{L}\p{M}\u200C\u200D]+"""
    r"""| ?\p{N}+"""
    r"""| ?[^\s\p{L}\p{M}\p{N}\u200C\u200D]+"""
    r"""|\s*[\r\n]+"""
    r"""|\s+(?!\S)"""
    r"""|\s+"""
)


def iter_text_segments(text: str) -> Iterator[str]:
    """Text between <|endoftext|> markers (the markers themselves are dropped)."""
    yield from text.split(EOT_TOKEN)


def iter_file_segments(path: Path, show_progress: bool = False) -> Iterator[str]:
    """Same as iter_text_segments for a file, streamed in blocks so the corpus never sits in memory."""
    path = Path(path)
    carry = ""
    with path.open("r", encoding="utf-8", newline="") as f, tqdm(
        total=path.stat().st_size, unit="B", unit_scale=True, desc=path.name, disable=not show_progress
    ) as bar:
        while block := f.read(READ_CHARS):
            bar.update(len(block.encode("utf-8")))
            parts = (carry + block).split(EOT_TOKEN)
            carry = parts.pop()
            yield from parts
    yield carry


def count_words(segments: Iterable[str], pattern: regex.Pattern) -> Counter[bytes]:
    """Frequency of every distinct pre-tokenised word, as UTF-8 bytes."""
    counts: Counter[str] = Counter()
    for segment in segments:
        counts.update(pattern.findall(segment))
    return Counter({word.encode("utf-8"): n for word, n in counts.items()})


def list_words(segments: Iterable[str], pattern: regex.Pattern) -> list[bytes]:
    """Every pre-tokenised word occurrence, in order, as UTF-8 bytes."""
    return [word.encode("utf-8") for segment in segments for word in pattern.findall(segment)]
