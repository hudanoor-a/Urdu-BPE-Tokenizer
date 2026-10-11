"""Encode train.txt and val.txt with the final tokenizer into train.bin and val.bin. PLACEHOLDER.

Usage:
    python -m urdu_bpe.encode_corpus [--tokenizer artifacts/tokenizer.json] [--corpus-dir corpus] [--out-dir artifacts]

Output: <out-dir>/train.bin and <out-dir>/val.bin, flat NumPy arrays of dtype uint16 (IDs 0-49,999),
readable with np.fromfile(path, dtype=np.uint16). The next assignment reads these files directly.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from .bpe import BPETokenizer

SPLITS = ("train", "val")
DTYPE = np.uint16


def encode_file(tok: BPETokenizer, src: Path, dst: Path) -> int:
    """Encode src into dst and return the number of tokens written.

    TODO:
      - stream src with pretokenize.iter_file_segments (train.txt is ~1 GB; never load it whole)
      - encode each segment and write ID 256 between segments, so the result equals tok.encode(whole file)
      - convert batches to np.asarray(ids, dtype=DTYPE) and append them to dst with .tofile(f)
      - check max(id) < 2**16 before casting
    """
    raise NotImplementedError("TODO")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tokenizer", type=Path, default=Path("artifacts/tokenizer.json"))
    ap.add_argument("--corpus-dir", type=Path, default=Path("corpus"))
    ap.add_argument("--out-dir", type=Path, default=Path("artifacts"))
    args = ap.parse_args()

    tok = BPETokenizer.load(args.tokenizer)
    for split in SPLITS:
        n = encode_file(tok, args.corpus_dir / f"{split}.txt", args.out_dir / f"{split}.bin")
        print(f"{split}: {n:,} tokens -> {args.out_dir / f'{split}.bin'}")


if __name__ == "__main__":
    main()
