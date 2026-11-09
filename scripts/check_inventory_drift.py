#!/usr/bin/env python3
"""Fail if the frozen 48-case pack drifts, or if a file invents agreement.

The public tree is a blind task pack: packets, an id manifest, and empty
templates. It does not contain completed labels or an inter-annotator
agreement number. This script checks the things that can quietly go wrong:

- ``packets/``, ``semantic-sample.json``, and both annotator templates must
  list the same 48 ids, in the same order, and the templates must still be
  empty.
- ``verification.json`` must keep ``agreement`` null and
  ``annotations_completed`` false. A hand-written kappa belongs in a later
  change that also replaces this gate, after real submissions exist.
- Prose and JSON outside this file must not state a numeric kappa.

Usage:
    python3 scripts/check_inventory_drift.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN_PACKET_COUNT = 48
THIS_FILE = "scripts/check_inventory_drift.py"

# Numeric agreement claims. Bare mentions ("kappa is not computed") are fine.
AGREEMENT_PATTERNS = [
    re.compile(r"(?i)\bkappa\b[^\n]{0,40}\d+\.\d+"),
    re.compile(r"(?i)\bkappa\b\s*[:=]\s*-?\d"),
    re.compile(r"κ[^\n]{0,20}\d+\.\d+"),
    re.compile(r"κ\s*[:=]\s*-?\d"),
    re.compile(r"(?i)\"(?:cohen_|fleiss_)?kappa\"\s*:\s*-?\d"),
    re.compile(r"(?i)\b(?:cohen|fleiss)\b[^\n]{0,40}\d+\.\d+"),
]


def agreement_hits(text: str) -> list[str]:
    hits = []
    for pattern in AGREEMENT_PATTERNS:
        match = pattern.search(text)
        if match:
            hits.append(match.group(0))
    return hits


def _self_test_patterns() -> None:
    """The detector has to fire on invented numbers and stay quiet on refusals."""
    assert agreement_hits("Cohen's kappa = 0.81")
    assert agreement_hits('{"kappa": 0.5}')
    assert agreement_hits("κ = 0.72")
    assert not agreement_hits("No Cohen's κ is reported because annotation has not been run.")
    assert not agreement_hits("kappa is not computed; 48 packets remain unlabeled")


def load_json(path: Path, errors: list[str]):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path.relative_to(ROOT).as_posix()}: {exc}")
        return None


def read_jsonl(path: Path, errors: list[str]) -> list[dict]:
    rows = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        errors.append(f"{path.relative_to(ROOT).as_posix()}: {exc}")
        return rows
    for n, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path.name}:{n}: {exc}")
            continue
        if not isinstance(row, dict):
            errors.append(f"{path.name}:{n}: row must be an object")
            continue
        rows.append(row)
    return rows


def check_templates(role: str, path: Path, expected_ids: list[str], errors: list[str]) -> int:
    rows = read_jsonl(path, errors)
    got = [str(row.get("sample_id", "")) for row in rows]
    if got != expected_ids:
        errors.append(
            f"{path.name}: sample_id sequence must match semantic-sample.json "
            f"({len(got)} rows, frozen {len(expected_ids)})"
        )
    for n, row in enumerate(rows, 1):
        if row.get("annotator") != role:
            errors.append(f"{path.name}:{n}: annotator must be {role}")
        if row.get("labels") != []:
            errors.append(
                f"{path.name}:{n}: template labels must stay empty; "
                "completed work does not belong in the template"
            )
        if row.get("rationale") != "":
            errors.append(f"{path.name}:{n}: template rationale must stay empty")
        extra = set(row) - {"annotator", "sample_id", "labels", "rationale"}
        if extra:
            errors.append(f"{path.name}:{n}: unexpected keys {sorted(extra)}")
    return len(rows)


def check_verification(packet_count: int, template_a: int, template_b: int, adj_bytes: int, errors: list[str]) -> None:
    path = ROOT / "verification.json"
    doc = load_json(path, errors)
    if not isinstance(doc, dict):
        return
    expected = {
        "study_status": "work_in_progress",
        "annotations_completed": False,
        "agreement": None,
        "packet_count": packet_count,
        "sample_count": packet_count,
        "template_a_rows": template_a,
        "template_b_rows": template_b,
        "adjudication_template_bytes": adj_bytes,
        "synthetic_fixture_notice_present": True,
    }
    for key, want in expected.items():
        if doc.get(key) != want:
            errors.append(f"verification.json {key}={doc.get(key)!r}; expected {want!r}")
    ok_means = str(doc.get("ok_means", ""))
    if doc.get("ok") is True and "agreement" not in ok_means:
        errors.append("verification.json ok=true must say that ok is not an agreement statistic")
    for banned in ("cohen_kappa", "fleiss_kappa", "kappa"):
        if banned in doc and doc[banned] not in (None,):
            errors.append(f"verification.json must not carry {banned}")


def scan_agreement_claims(errors: list[str]) -> None:
    skip_dirs = {".git", "__pycache__", ".github"}
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in skip_dirs for part in rel.parts) or rel.suffix == ".pyc":
            continue
        if rel.as_posix() == THIS_FILE:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        hits = agreement_hits(text)
        if hits:
            errors.append(f"{rel.as_posix()}: numeric agreement claim {hits[0]!r}")


def main() -> int:
    _self_test_patterns()
    errors: list[str] = []

    sample_path = ROOT / "semantic-sample.json"
    sample = load_json(sample_path, errors)
    expected_ids: list[str] = []
    if isinstance(sample, dict):
        episodes = sample.get("episodes")
        if not isinstance(episodes, list):
            errors.append("semantic-sample.json: episodes must be a list")
            episodes = []
        if sample.get("sample_size") != FROZEN_PACKET_COUNT:
            errors.append(
                f"semantic-sample.json sample_size={sample.get('sample_size')!r}; "
                f"frozen count is {FROZEN_PACKET_COUNT}"
            )
        if sample.get("requested_size") != FROZEN_PACKET_COUNT:
            errors.append(
                f"semantic-sample.json requested_size={sample.get('requested_size')!r}; "
                f"frozen count is {FROZEN_PACKET_COUNT}"
            )
        if sample.get("seed") != 17:
            errors.append(f"semantic-sample.json seed={sample.get('seed')!r}; frozen seed is 17")
        orders = []
        for row in episodes:
            if not isinstance(row, dict):
                errors.append("semantic-sample.json: episode row is not an object")
                continue
            sid = str(row.get("sample_id", ""))
            if not re.fullmatch(r"[0-9a-f]{16}", sid):
                errors.append(f"semantic-sample.json: bad sample_id {sid!r}")
            expected_ids.append(sid)
            orders.append(row.get("blind_order"))
        if len(expected_ids) != len(set(expected_ids)):
            errors.append("semantic-sample.json: duplicate sample_id")
        if len(expected_ids) != FROZEN_PACKET_COUNT:
            errors.append(
                f"semantic-sample.json has {len(expected_ids)} episodes; frozen count is {FROZEN_PACKET_COUNT}"
            )
        if orders != list(range(FROZEN_PACKET_COUNT)):
            errors.append("semantic-sample.json blind_order must be 0..47 in that order")

    packet_dir = ROOT / "packets"
    packet_ids = sorted(p.stem for p in packet_dir.glob("*.json")) if packet_dir.is_dir() else []
    if packet_ids != sorted(expected_ids):
        missing = sorted(set(expected_ids) - set(packet_ids))
        extra = sorted(set(packet_ids) - set(expected_ids))
        errors.append(
            f"packets/ has {len(packet_ids)} json files; manifest has {len(expected_ids)}. "
            f"missing={missing[:5]} extra={extra[:5]}"
        )
    for sid in expected_ids:
        path = packet_dir / f"{sid}.json"
        if not path.is_file():
            continue
        doc = load_json(path, errors)
        if not isinstance(doc, dict):
            continue
        if doc.get("sample_id") != sid:
            errors.append(f"packets/{sid}.json sample_id={doc.get('sample_id')!r}")
        notice = str(doc.get("data_notice", ""))
        if "synthetic" not in notice:
            errors.append(f"packets/{sid}.json data_notice must say the fixture is synthetic")

    template_a = check_templates("A", ROOT / "annotator-a-template.jsonl", expected_ids, errors)
    template_b = check_templates("B", ROOT / "annotator-b-template.jsonl", expected_ids, errors)

    adj = ROOT / "adjudication-template.jsonl"
    try:
        adj_bytes = adj.stat().st_size
    except OSError as exc:
        errors.append(f"adjudication-template.jsonl: {exc}")
        adj_bytes = -1
    if adj_bytes != 0:
        errors.append(
            f"adjudication-template.jsonl is {adj_bytes} bytes; it stays empty until "
            "real disagreements exist"
        )

    if len(packet_ids) == FROZEN_PACKET_COUNT:
        check_verification(FROZEN_PACKET_COUNT, template_a, template_b, adj_bytes, errors)
    scan_agreement_claims(errors)

    readme = ROOT / "README.md"
    try:
        readme_text = readme.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"README.md: {exc}")
        readme_text = ""
    if "WORK-IN-PROGRESS" not in readme_text:
        errors.append("README.md must keep STATUS: WORK-IN-PROGRESS while annotations are absent")
    problem = ""
    if "## Problem" in readme_text:
        after = readme_text.split("## Problem", 1)[1]
        problem = after.split("\n## ", 1)[0]
        problem_lines = [line for line in problem.splitlines() if line.strip()]
        if len(problem_lines) > 3:
            errors.append(f"README.md Problem section has {len(problem_lines)} non-empty lines; limit is 3")
    else:
        errors.append("README.md needs a Problem section of at most 3 lines")

    if errors:
        for err in errors:
            print(f"[FAIL] {err}")
        print(f"INVENTORY DRIFT = FAIL ({len(errors)} problem(s))")
        return 1

    print(
        f"[PASS] {FROZEN_PACKET_COUNT} packets match semantic-sample.json "
        f"and empty templates A/B ({template_a}/{template_b} ids)"
    )
    print("[PASS] adjudication template is empty")
    print("[PASS] verification.json agreement is null and annotations_completed is false")
    print("[PASS] no numeric agreement claim")
    print("INVENTORY DRIFT = PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
