#!/usr/bin/env python3
"""Regenerate SHA256SUMS over the release tree.

The committed SHA256SUMS went stale (it listed a hash for CONTRIBUTING.md that no
longer matched the file), which made `sha256sum -c` fail and took the whole
integrity claim down with it. This script regenerates the list from the files
actually present, so the two can never drift again.

Usage:
    python3 scripts/gen_sha256sums.py            # write SHA256SUMS
    python3 scripts/gen_sha256sums.py --check    # verify only, non-zero on drift
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMS = ROOT / "SHA256SUMS"

EXCLUDE_DIRS = {".git", "__pycache__", ".github"}
EXCLUDE_NAMES = {"SHA256SUMS"}


def iter_files():
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if rel.name in EXCLUDE_NAMES or rel.suffix == ".pyc":
            continue
        yield rel.as_posix(), path


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify instead of writing")
    args = parser.parse_args()

    entries = [(rel, digest(path)) for rel, path in iter_files()]
    body = "".join(f"{sha}  {rel}\n" for rel, sha in entries)

    if args.check:
        current = SUMS.read_text(encoding="utf-8") if SUMS.exists() else ""
        if current != body:
            print("SHA256SUMS is out of date -- run: python3 scripts/gen_sha256sums.py")
            return 1
        print(f"SHA256SUMS matches {len(entries)} files")
        return 0

    SUMS.write_text(body, encoding="utf-8")
    print(f"wrote SHA256SUMS with {len(entries)} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
