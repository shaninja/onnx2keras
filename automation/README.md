# Op Manager V1

This package is the repo-local starting point for the scripted Claude↔Codex workflow described in [the design spec](../docs/superpowers/specs/2026-04-17-op-manager-v1-design.md).

## What exists in v1

- persisted run records under `automation/runs/`
- a small CLI in `automation/manager.py`
- typed state models and JSON-backed storage
- Claude/Codex result parsing rules
- fork-safe pull request argument helpers for `shaninja/onnx2keras`

## Current CLI

Start a run:

```bash
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python poetry run python -m automation.manager start --op CastLike
```

Inspect an existing run:

```bash
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python poetry run python -m automation.manager status --run-file automation/runs/<run-id>/run.json
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python poetry run python -m automation.manager resume --run-file automation/runs/<run-id>/run.json
```

To test without writing run data under the repo:

```bash
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python poetry run python -m automation.manager start \
  --op CastLike \
  --runs-root /tmp/op-manager-runs \
  --repo-root /home/shani/onnx2keras/onnx2keras
```

Expected output is a JSON status payload similar to:

```json
{
  "branch_name": "add/castlike",
  "ci_round": 0,
  "op_name": "CastLike",
  "pr_number": null,
  "review_round": 0,
  "run_id": "20260417-142849-castlike",
  "state": "PREPARE_WORKTREE"
}
```

## Process Visibility

Current visibility is intentionally simple:

- the CLI prints a JSON status payload
- each run persists `run.json`
- each run creates artifact directories for future Claude, Codex, and CI outputs
- `status` and `resume` read the same persisted run file

There is no live progress log yet. The next layer should add:

- `logs/manager.log` with one line per state transition
- captured stdout/stderr for Claude and Codex subprocesses
- per-round artifacts under `artifacts/claude/`, `artifacts/codex/`, and `artifacts/ci/`
- clear terminal progress messages while a long-running manager process is active

## Current Limitations

The current implementation is a manager skeleton. It does not yet:

- invoke Claude or Codex subprocesses
- prepare git worktrees
- commit, push, or open pull requests
- poll CI or route CI failures back into the review loop
- schedule multiple ops concurrently

## Future Direction

The intended next layers are:

1. subprocess invocation for Claude and Codex with fixed output paths
2. manager-owned git and `gh` actions
3. CI polling and remediation rounds
4. a scheduler that can assign multiple ops while minimizing conflicts

All future work should stay consistent with the design and implementation plan under `docs/superpowers/`.

## Verification

Run the automation tests with:

```bash
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python poetry run python -m pytest -q test/automation
```

The initial skeleton was verified with that command and a temporary CLI smoke run using `/tmp/op-manager-runs`.
