# FAILURE_MODES

**STATUS: WORK-IN-PROGRESS — not a finished study yet.** The gaps below are why this repository stays a task pack. Nothing here is a measured agreement result.

## Label whitelist gaming

`scripts/validate_submission.py` accepts any non-empty subset of the eight allowed labels when `rationale` is at least 12 characters and is not exactly the label text. That is a format check. It does not decide whether the label is true, and it cannot tell a person from a script that emits a whitelist label plus filler prose.

The shipped templates have `labels: []`. An untouched copy fails validation (`labels must be nonempty`). Filling those arrays is still not evidence that a judgment was made. Completed rows, when they exist, belong in a local `annotations-a.jsonl` or `annotations-b.jsonl`, which this release does not contain.

## Blinding leaks

Annotators are supposed to see the prompt, the tool sequence, and the persisted state diff. They are not supposed to see which guard produced the episode, whether the benchmark counted it, how the contract checks scored it, the episode id, or the model identity. `scripts/check_blind_integrity.py` scans the tree (the checker file itself is the only allowlisted path) and exits non-zero on those answer-axis strings and on credential-shaped tokens.

The scan does not prove an annotator never saw the axis outside this repository. An earlier checker only walked `packets/` and reported success while the manifest still carried the axis; the current script walks the whole release so that class of miss fails closed.

A second leak is social. If annotator A's file lands in the tree before annotator B locks theirs, B can read A's labels. `annotations-a.jsonl`, `annotations-b.jsonl`, and `adjudication.jsonl` are gitignored for that reason. `CONTRIBUTING.md` tells contributors to send those files to the maintainer instead of publishing one side first.

## Unfinished annotations

What is in the tree today:

- 48 packets and a blinded manifest of the same 48 ids.
- Annotator A and B templates with those ids and empty labels.
- An empty `adjudication-template.jsonl`, because the disagreement set is unknown.
- No completed submission and no adjudication file.
- No inter-annotator agreement. `verification.json` keeps `agreement` null. `ok: true` means a blind-integrity snapshot passed. `scripts/check_inventory_drift.py` rejects a numeric kappa pasted into the docs or into that file.

The upstream command `tools/verify_approval_semantic.py` is not in this repository. A clone cannot run it and has no output from it.

## Gaps before this can be called finished

- [ ] Annotator A submits 48 validated rows, produced independently.
- [ ] Annotator B submits 48 validated rows, still blinded to A.
- [ ] A third person adjudicates the disagreements.
- [ ] Agreement is computed from those files by the upstream tool, then recorded. Until that exists, do not write a kappa by hand.

`scripts/check_inventory_drift.py` keeps the packet count at 48, checks that both templates match those ids, and refuses `annotations_completed: true` or a non-null `agreement` in `verification.json`. Changing that gate is part of finishing the study, not a substitute for it.
