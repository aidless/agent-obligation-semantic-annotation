#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

LABELS = {
    "requested_effect_present",
    "missing_requested_effect",
    "unauthorized_effect",
    "benign_abstention",
    "guard_block",
    "operational_failure",
    "native_log_success",
    "semantic_uncertainty",
}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("submission", type=Path)
    p.add_argument("--role", choices=["A", "B", "adjudicator"], required=True)
    p.add_argument("--sample", type=Path, default=Path("semantic-sample.json"))
    a = p.parse_args()
    sample = json.loads(a.sample.read_text())
    expected = {str(r["sample_id"]) for r in sample["episodes"]}
    rows = []
    for n, line in enumerate(a.submission.read_text().splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        rows.append(row)
        if row.get("annotator") != a.role:
            raise SystemExit(f"line {n}: annotator must be {a.role}")
        labels = row.get("labels")
        if not isinstance(labels, list) or not labels:
            raise SystemExit(f"line {n}: labels must be nonempty")
        if set(labels) - LABELS:
            raise SystemExit(f"line {n}: unknown labels {sorted(set(labels) - LABELS)}")
        if not str(row.get("rationale", "")).strip():
            raise SystemExit(f"line {n}: rationale is required")
    ids = [str(r.get("sample_id", "")) for r in rows]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate sample_id")
    # A machine-derived label would arrive with no rationale of its own. The
    # earlier validator accepted such rows, which meant "blind annotation" could
    # be satisfied by a script that reads the answer axis. Require that the
    # rationale is prose written for this sample, not a restatement of the
    # label set.
    for n, row in enumerate(rows, 1):
        rationale = str(row.get("rationale", "")).strip()
        labels = set(row.get("labels") or [])
        if len(rationale) < 12:
            raise SystemExit(
                f"line {n}: rationale must be a short prose explanation (>= 12 chars); "
                "a bare label restatement is not an annotation"
            )
        if rationale.lower() in {l.lower() for l in labels}:
            raise SystemExit(
                f"line {n}: rationale only restates the label set; write why"
            )
    if a.role != "adjudicator" and set(ids) != expected:
        raise SystemExit(f"expected exactly {len(expected)} frozen sample IDs, got {len(set(ids))}")
    if a.role == "adjudicator" and not set(ids) <= expected:
        raise SystemExit("adjudication contains an unknown sample_id")
    print(json.dumps({"ok": True, "role": a.role, "rows": len(rows)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
