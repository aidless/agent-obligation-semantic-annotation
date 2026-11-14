"""Offline tests for validate_submission.py.

Covers the validator's contract without any annotator work:
- a compliant A submission (48 rows, all frozen IDs, allowed labels) passes;
- a submission with wrong role is rejected;
- an unfilled template (empty labels) is rejected;
- duplicate sample_ids are rejected;
- an adjudication may be a subset of the frozen IDs.

These run offline: no network, no annotator judgement needed.
"""
import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
VALIDATOR = REPO / "scripts" / "validate_submission.py"
SAMPLE = REPO / "semantic-sample.json"


def _run(role, rows):
    """Run the validator against an in-memory row list, return (rc, stdout)."""
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
        path = f.name
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR), path, "--role", role],
        capture_output=True, text=True, cwd=str(REPO),
    )
    Path(path).unlink()
    return proc.returncode, proc.stdout


def _all_rows(annotator="A", label="semantic_uncertainty"):
    sample = json.loads(SAMPLE.read_text())
    return [
        {"annotator": annotator, "sample_id": str(ep["sample_id"]),
         "labels": [label], "rationale": "offline test fixture"}
        for ep in sample["episodes"]
    ]


def test_compliant_a_passes():
    rc, out = _run("A", _all_rows())
    assert rc == 0, out
    assert json.loads(out)["rows"] == 48


def test_compliant_b_passes():
    rc, out = _run("B", _all_rows(annotator="B"))
    assert rc == 0, out


def test_wrong_role_rejected():
    rc, _ = _run("B", _all_rows(annotator="A"))
    assert rc != 0


def test_empty_labels_rejected():
    rows = _all_rows()
    rows[0]["labels"] = []
    rc, _ = _run("A", rows)
    assert rc != 0


def test_unknown_label_rejected():
    rows = _all_rows()
    rows[0]["labels"] = ["not_a_real_label"]
    rc, _ = _run("A", rows)
    assert rc != 0


def test_duplicate_sample_id_rejected():
    rows = _all_rows()
    rows[1]["sample_id"] = rows[0]["sample_id"]
    rc, _ = _run("A", rows)
    assert rc != 0


def test_missing_rationale_rejected():
    rows = _all_rows()
    rows[0].pop("rationale", None)
    rc, _ = _run("A", rows)
    assert rc != 0


def test_adjudicator_subset_ok():
    rows = _all_rows(annotator="adjudicator")
    rc, out = _run("adjudicator", rows[:10])
    assert rc == 0, out


def test_adjudicator_unknown_id_rejected():
    rows = _all_rows(annotator="adjudicator")
    rows.append({"annotator": "adjudicator", "sample_id": "deadbeef",
                 "labels": ["semantic_uncertainty"], "rationale": "x"})
    rc, _ = _run("adjudicator", rows)
    assert rc != 0


def test_frozen_sample_has_48_ids():
    sample = json.loads(SAMPLE.read_text())
    assert len(sample["episodes"]) == 48
    assert len({str(ep["sample_id"]) for ep in sample["episodes"]}) == 48


def test_packet_dir_matches_frozen_sample():
    packets = {p.stem for p in (REPO / "packets").glob("*.json")}
    sample = json.loads(SAMPLE.read_text())
    frozen = {str(ep["sample_id"]) for ep in sample["episodes"]}
    assert packets == frozen
