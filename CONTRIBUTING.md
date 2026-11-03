# Contributing annotations

1. Claim role A or B before reading packets. Do not take both roles.
2. Work independently and avoid case-level discussion until both JSONL files are locked.
3. Fill every sample exactly once. Use only labels listed in README.md.
4. Keep rationale concise and evidence based.
5. Submit only your completed JSONL. Do not modify packets or the frozen sample.
6. A third person adjudicates disagreements after both primary files are complete.

## Public GitHub workflow

1. Open **Claim an annotator role** and claim A or B. The maintainer assigns at most one person per role.
2. Fork the repository and work locally. Do not publish case-level labels in an issue.
3. Add exactly one file: `annotations-a.jsonl` or `annotations-b.jsonl`.
4. Open a pull request. Automated validation checks all 48 IDs, allowed labels, nonempty rationales, role identity, and duplicates.
5. The maintainer should avoid merging the first primary annotation file until the second annotator has locked their work. This prevents accidental unblinding.
6. After A and B are locked, disagreements are given to a third person through `adjudication.jsonl`.

## Before you open a pull request

```bash
python3 scripts/check_blind_integrity.py   # no answer axis may be visible
python3 scripts/gen_sha256sums.py --check   # SHA256SUMS must be current
python3 scripts/validate_submission.py annotations-a.jsonl --role A
```

Your submission file (`annotations-a.jsonl` / `annotations-b.jsonl`) must **not** be
committed while the other annotator is still working — landing one file un-blinds the
other. These paths are git-ignored on purpose; send the file to the maintainer directly.
