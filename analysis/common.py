"""Helpers shared by the analysis scripts."""

from __future__ import annotations

from pathlib import Path

OUT_DIR = Path("analysis/output")
VISIBLE_SPACE = "␣"


def show(token: bytes) -> str:
    """Printable form of a token: invalid UTF-8 bytes as \\xNN, space as a visible symbol, | escaped."""
    text = token.decode("utf-8", errors="backslashreplace")
    return text.replace(" ", VISIBLE_SPACE).replace("\n", "\\n").replace("|", "\\|")


def md_table(header: list[str], rows: list[list]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines) + "\n"


def write_output(name: str, sections: list[str]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    path.write_text("\n".join(sections), encoding="utf-8", newline="\n")
    return path
