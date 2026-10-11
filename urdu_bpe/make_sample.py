"""Cut a sample of whole documents (about 1 MB) from train.txt, for testing the trainers.

Usage:
    python -m urdu_bpe.make_sample [--train corpus/train.txt] [--out data/sample_1mb.txt] [--min-bytes 1000000] [--seed 42]

Seeks to a random byte offset (fixed seed), starts after the next <|endoftext|> line and takes
whole documents until at least --min-bytes.
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

from .pretokenize import EOT_TOKEN

SEPARATOR = f"{EOT_TOKEN}\n".encode("utf-8")
CHUNK = 1 << 20


def take_sample(path: Path, min_bytes: int, seed: int) -> tuple[bytes, int]:
    """Return (sample bytes, random offset). The sample starts and ends on a document boundary."""
    size = path.stat().st_size
    if size <= 4 * min_bytes:
        raise SystemExit(f"{path} is too small for a {min_bytes:,}-byte sample")
    offset = random.Random(seed).randrange(size - 4 * min_bytes)
    buf, start = b"", -1
    with path.open("rb") as f:
        f.seek(offset)
        while chunk := f.read(CHUNK):
            buf += chunk
            if start < 0:
                i = buf.find(SEPARATOR)
                if i < 0:
                    continue
                start = i + len(SEPARATOR)
            end = buf.find(SEPARATOR, start + min_bytes - len(SEPARATOR))
            if end >= 0:
                return buf[start : end + len(SEPARATOR)], offset
    raise SystemExit("reached the end of the file before collecting enough documents")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--train", type=Path, default=Path("corpus/train.txt"))
    ap.add_argument("--out", type=Path, default=Path("data/sample_1mb.txt"))
    ap.add_argument("--min-bytes", type=int, default=1_000_000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    sample, offset = take_sample(args.train, args.min_bytes, args.seed)
    sample.decode("utf-8")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(sample)
    print(f"wrote {args.out}: {len(sample):,} bytes, {sample.count(SEPARATOR)} documents, from offset {offset:,}")


if __name__ == "__main__":
    main()
