#!/usr/bin/env python3
"""Fail-closed blind-integrity check for the annotation release.

The blind annotation task only works if the annotator cannot recover the answer
axis from anything shipped in this repository. This script scans EVERY shipped
file -- not just ``packets/`` -- for the answer-axis terms and for credential
patterns, and exits non-zero when any of them leak.

The previous verification.json reported ``ok: true`` while ``semantic-sample.json``
still carried ``arm`` / ``native_utility`` / ``strict_clean`` / ``minimal_clean``
/ ``stratum`` / ``episode_id``. The checker must therefore cover the whole
release tree, not a subdirectory.

Usage:
    python3 scripts/check_blind_integrity.py
    python3 scripts/check_blind_integrity.py --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Terms that expose the answer axis or the model/guard identity.
BLIND_TERMS = [
    "no_gate",
    "name_log_gate",
    "deny_all",
    "exact_persisted_effect_verifier",
    "native_utility",
    "strict_clean",
    "minimal_clean",
    "relation_group",
    "model_slot",
    "blind_order_missing",
    "north-mini",
    "nemotron",
    "openrouter",
    "magpie",
]

# Credential shapes. The packets are synthetic fixtures, but a fixture that
# looks like a live credential would be copied by contributors.
CREDENTIAL_PATTERNS = [
    r"sk-[A-Za-z0-9_\-]{32,}",
    r"\bAKIA[0-9A-Z]{16}\b",
    r"\bgh[pousr]_[A-Za-z0-9]{30,}\b",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"(?i)authorization\s*[:=]\s*[\"']?bearer\s+\S+",
    r"(?i)\bapi[_-]?key\s*[:=]\s*[\"'][^\"'\s]{16,}[\"']",
]

# Files that legitimately discuss the blind terms in prose: this script and the
# release notes that explain what was blinded. They are excluded from the scan
# by exact relative path, not by pattern.
ALLOWED_FILES = {
    "scripts/check_blind_integrity.py",
}


def iter_files():
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in ALLOWED_FILES:
            continue
        if rel.startswith(".git/") or "/__pycache__/" in rel or rel.endswith(".pyc"):
            continue
        yield rel, path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    args = parser.parse_args()

    errors: list[dict] = []
    scanned = 0
    term_hits: dict[str, list[str]] = {}
    cred_hits: dict[str, list[str]] = {}

    for rel, path in iter_files():
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        scanned += 1
        for term in BLIND_TERMS:
            if term in text:
                term_hits.setdefault(term, []).append(rel)
        for pattern in CREDENTIAL_PATTERNS:
            for match in re.finditer(pattern, text):
                cred_hits.setdefault(pattern, []).append(f"{rel}:{text.count(chr(10), 0, match.start()) + 1}")

    for term, files in term_hits.items():
        errors.append({
            "kind": "blind_term_leak",
            "term": term,
            "files": sorted(set(files)),
            "detail": "answer-axis or model-identity term is visible to the annotator",
        })
    for pattern, places in cred_hits.items():
        errors.append({
            "kind": "credential_pattern",
            "pattern": pattern,
            "files": sorted(set(places)),
            "detail": "credential-shaped string shipped in the release",
        })

    # The report deliberately does NOT echo the term list: shipping a file that
    # names every blind term would itself trip the next scan of this repo.
    result = {
        "schema": "blind-integrity-check/1",
        "files_scanned": scanned,
        "blind_terms_checked_count": len(BLIND_TERMS),
        "credential_patterns_checked_count": len(CREDENTIAL_PATTERNS),
        "errors": errors,
        "ok": not errors,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"scanned {scanned} files")
        if errors:
            for err in errors:
                print(f"[FAIL] {err['kind']}: {err.get('term') or err.get('pattern')} in {err['files']}")
            print(f"BLIND INTEGRITY = FAIL ({len(errors)} problem(s))")
        else:
            print("[PASS] no blind-term leak")
            print("[PASS] no credential pattern")
            print("BLIND INTEGRITY = PASS")

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
