"""Sanity-check the cleaned corpus before BPE training.

Usage:
    python -m urdu_corpus.check_corpus [--corpus-dir corpus] [--keep-zwnj] [--digits ascii|urdu|arabic-indic]

Streams train.txt, val.txt and test.txt line by line, prints details per file and a PASS/FAIL
summary, and exits with code 1 if any check failed. Nothing is modified.
"""

from __future__ import annotations

import argparse
import random
import re
import sys
from collections import Counter
from pathlib import Path

from tqdm import tqdm

SPLITS = ("train.txt", "val.txt", "test.txt")
EOT_BYTES = b"<|endoftext|>"
BOM = b"\xef\xbb\xbf"
SEED = 42
N_SAMPLES = 5
SAMPLE_CHARS = 200
TAIL_BYTES = 100
ZWNJ = "\u200C"

BANNED = {
    "\u064A": "ARABIC YEH (should be U+06CC)",
    "\u0649": "ALEF MAKSURA (should be U+06CC)",
    "\u0643": "ARABIC KAF (should be U+06A9)",
    "\u0647": "ARABIC HEH (should be U+06C1)",
    "\u0640": "TATWEEL",
    "\u200B": "ZERO WIDTH SPACE",
    "\u200C": "ZWNJ",
    "\u200D": "ZWJ",
    "\u200E": "LEFT-TO-RIGHT MARK",
    "\u200F": "RIGHT-TO-LEFT MARK",
    "\uFEFF": "BOM / ZWNBSP",
    "\u00A0": "NO-BREAK SPACE",
    "\u202A": "LRE",
    "\u202B": "RLE",
    "\u202C": "PDF",
    "\u202D": "LRO",
    "\u202E": "RLO",
}

DIGIT_RANGES = {
    "ascii": ("0", "9", "ASCII digits 0-9"),
    "arabic-indic": ("\u0660", "\u0669", "Arabic-Indic digits U+0660-0669"),
    "urdu": ("\u06F0", "\u06F9", "Extended Arabic-Indic digits U+06F0-06F9"),
}

Row = tuple[str, str, str, str]


def digit_chars(key: str) -> set[str]:
    lo, hi, _ = DIGIT_RANGES[key]
    return {chr(c) for c in range(ord(lo), ord(hi) + 1)}


def build_pattern(forbidden_digits: list[str]) -> re.Pattern[str]:
    """One character class for every watched code point, so each line is scanned once."""
    parts = [re.escape(ch) for ch in BANNED]
    parts += [f"{re.escape(DIGIT_RANGES[k][0])}-{re.escape(DIGIT_RANGES[k][1])}" for k in forbidden_digits]
    return re.compile("[" + "".join(parts) + "]")


def scan_file(path: Path, pattern: re.Pattern[str]) -> dict:
    """One streaming pass: strict UTF-8 decode, CR and marker counts, watched code points."""
    size = path.stat().st_size
    s = {"size": size, "lines": 0, "bad_utf8_lines": 0, "first_bad": None, "cr_lines": 0, "eot_count": 0, "eot_lines": 0, "chars": Counter()}
    with path.open("rb") as f:
        s["bom"] = f.read(3) == BOM
        f.seek(0)
        with tqdm(total=size, unit="B", unit_scale=True, desc=path.name, leave=False) as bar:
            pending = 0
            for lineno, raw in enumerate(f, start=1):
                s["lines"] += 1
                if b"\r" in raw:
                    s["cr_lines"] += 1
                if n := raw.count(EOT_BYTES):
                    s["eot_count"] += n
                    s["eot_lines"] += 1
                try:
                    text = raw.decode("utf-8")
                except UnicodeDecodeError as e:
                    s["bad_utf8_lines"] += 1
                    s["first_bad"] = s["first_bad"] or (lineno, str(e))
                    text = raw.decode("utf-8", errors="replace")
                if hits := pattern.findall(text):
                    s["chars"].update(hits)
                pending += len(raw)
                if pending >= 1 << 22:
                    bar.update(pending)
                    pending = 0
            bar.update(pending)
        f.seek(max(0, size - TAIL_BYTES))
        s["ends_with_eot"] = f.read().rstrip().endswith(EOT_BYTES)
    return s


def sample_lines(path: Path, rng: random.Random, k: int = N_SAMPLES) -> list[str]:
    """Seek to random byte offsets, drop the partial line, return the next whole line."""
    size = path.stat().st_size
    out: list[str] = []
    with path.open("rb") as f:
        for _ in range(k * 20):
            if len(out) == k:
                break
            f.seek(rng.randrange(size))
            f.readline()
            raw = f.readline()
            if raw.strip():
                text = raw.decode("utf-8", errors="replace").rstrip("\r\n")
                out.append(text if len(text) <= SAMPLE_CHARS else text[:SAMPLE_CHARS] + "...")
    return out


def check_file(name: str, s: dict, keep_zwnj: bool, digits: str, forbidden: list[str]) -> list[Row]:
    rows: list[Row] = [(name, "size", "INFO", f"{s['size'] / 1e6:.2f} MB, {s['lines']:,} lines")]

    # Byte-level BPE trains on raw bytes: invalid UTF-8 yields byte runs decode() cannot turn back
    # into text, and a BOM becomes a junk token glued to the first word.
    if s["bad_utf8_lines"]:
        ln, msg = s["first_bad"]
        rows.append((name, "utf8_strict", "FAIL", f"{s['bad_utf8_lines']:,} bad lines (first: line {ln}: {msg})"))
    else:
        rows.append((name, "utf8_strict", "PASS", "all lines decode"))
    rows.append((name, "no_bom", "FAIL" if s["bom"] else "PASS", "EF BB BF found" if s["bom"] else "none"))

    # normalize() emits LF only; a CR means the file went through platform newline translation and
    # every line break would reach BPE as \r\n.
    cr = s["cr_lines"]
    rows.append((name, "lf_newlines", "FAIL" if cr else "PASS", f"{cr:,} lines contain CR" if cr else "LF only"))

    # <|endoftext|> marks document boundaries; the trainer splits on it so no merge crosses documents.
    rows.append((name, "eot_count", "PASS" if s["eot_count"] else "FAIL", f"{s['eot_count']:,} markers on {s['eot_lines']:,} lines"))
    rows.append((name, "eot_at_end", "PASS" if s["ends_with_eot"] else "WARN", "yes" if s["ends_with_eot"] else "last document has no marker"))

    # Any code point normalisation should have removed gives one word several byte spellings,
    # wasting merges on variants that look identical on screen.
    chars = s["chars"]
    bad = [f"U+{ord(ch):04X}={chars[ch]:,}" for ch in BANNED if chars[ch] and not (ch == ZWNJ and keep_zwnj)]
    rows.append((name, "banned_codepoints", "FAIL" if bad else "PASS", ", ".join(bad) or "all 0"))
    if keep_zwnj:
        rows.append((name, "zwnj_count", "INFO", f"{chars[ZWNJ]:,}"))

    # Mixed digit scripts give every number two or three spellings.
    bad_digits = [f"{k}={n:,}" for k in forbidden if (n := sum(chars[c] for c in digit_chars(k)))]
    rows.append((name, f"foreign_digits({digits} kept)", "FAIL" if bad_digits else "PASS", ", ".join(bad_digits) or "all 0"))
    return rows


def print_summary(rows: list[Row]) -> bool:
    table = [("file", "check", "status", "detail")] + rows
    widths = [max(len(r[i]) for r in table) for i in range(3)]
    print("\n=== SUMMARY ===")
    for r in table:
        print("  ".join(c.ljust(w) for c, w in zip(r[:3], widths)) + "  " + r[3])
    failed = sum(r[2] == "FAIL" for r in rows)
    print(f"\nOVERALL: {'FAIL' if failed else 'PASS'} ({failed} failed checks)")
    return not failed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus-dir", type=Path, default=Path("corpus"))
    ap.add_argument("--keep-zwnj", action="store_true", help="ZWNJ is allowed; report its count as info")
    ap.add_argument("--digits", choices=sorted(DIGIT_RANGES), default="ascii", help="digit script the corpus was normalised to")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    forbidden = [k for k in DIGIT_RANGES if k != args.digits]
    pattern = build_pattern(forbidden)
    rng = random.Random(SEED)
    rows: list[Row] = []
    for name in SPLITS:
        path = args.corpus_dir / name
        if not path.is_file():
            rows.append((name, "exists", "FAIL", f"{path} not found"))
            continue
        s = scan_file(path, pattern)
        file_rows = check_file(name, s, args.keep_zwnj, args.digits, forbidden)
        rows += file_rows
        print(f"\n=== {name} ===")
        for _, check, status, detail in file_rows:
            print(f"  {check:<28} {status:<5} {detail}")
        print(f"  {N_SAMPLES} random lines (eyeball check for boilerplate, mixed scripts, broken extraction):")
        for i, line in enumerate(sample_lines(path, rng), 1):
            print(f"    [{i}] {line}")
    return 0 if print_summary(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
