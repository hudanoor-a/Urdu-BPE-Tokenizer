"""Urdu Unicode normalisation (cleaning step 2). Kept outside the tokenizer."""

from __future__ import annotations

import re
import unicodedata

ZWNJ_POLICIES = ("remove", "keep_between_letters")
ZWNJ_POLICY = "remove"

_CHAR_MAP = {
    "\u064A": "\u06CC",  # Arabic yeh -> Urdu yeh
    "\u0649": "\u06CC",  # alef maksura -> Urdu yeh
    "\u0643": "\u06A9",  # Arabic kaf -> Urdu kaf
    "\u06AA": "\u06A9",  # swash kaf -> Urdu kaf
    "\u0647": "\u06C1",  # Arabic heh -> gol heh (do-chashmi heh U+06BE is a different letter)
    "\u0629": "\u06C3",  # teh marbuta -> teh marbuta goal
    "\u066B": ".",  # Arabic decimal separator
    "\u066C": ",",  # Arabic thousands separator
    "\u066A": "%",  # Arabic percent sign
    **{chr(0x0660 + d): str(d) for d in range(10)},  # Arabic-Indic digits -> ASCII
    **{chr(0x06F0 + d): str(d) for d in range(10)},  # Extended Arabic-Indic digits -> ASCII
}
_TABLE = str.maketrans(_CHAR_MAP)

# Tatweel, harakat U+064B-0652, ZWSP, ZWJ, LRM/RLM, bidi controls, word joiner, BOM, soft hyphen,
# U+FFFD, Arabic letter mark and C0/C1 control characters (tab, LF and CR are handled below).
_REMOVE = re.compile(
    "[\u0640\u064B-\u0652\u200B\u200D-\u200F\u202A-\u202E\u2060\u2066-\u2069"
    "\uFEFF\u00AD\uFFFD\u061C\x00-\x08\x0e-\x1f\x7f-\x84\x86-\x9f]"
)
_LINE_BREAKS = re.compile(r"\r\n?|[\x0b\x0c\x85\u2028\u2029]")
_SPACES = re.compile(r"[ \t\u00A0\u1680\u2000-\u200A\u202F\u205F\u3000]+")
_ZWNJ_OUTSIDE_WORD = re.compile(r"(?<![^\W\d_])\u200C+|\u200C+(?![^\W\d_])")


def normalize(text: str, zwnj: str = ZWNJ_POLICY) -> str:
    """Return text with one spelling per Urdu letter, ASCII digits, single spaces and LF newlines."""
    if zwnj not in ZWNJ_POLICIES:
        raise ValueError(f"zwnj must be one of {ZWNJ_POLICIES}")
    text = unicodedata.normalize("NFKC", text)
    text = _LINE_BREAKS.sub("\n", text)
    text = _REMOVE.sub("", text.translate(_TABLE))
    if zwnj == "remove":
        text = text.replace("\u200C", "")
    else:
        text = _ZWNJ_OUTSIDE_WORD.sub("", text)
    text = _SPACES.sub(" ", text)
    return "\n".join(line for line in map(str.strip, text.split("\n")) if line)
