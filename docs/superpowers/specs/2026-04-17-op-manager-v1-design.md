# Op Manager V1 Design

## Purpose

Design a repo-local, script-driven workflow that automates the current manual loop for adding ONNX ops:

1. Create an isolated branch/worktree for one explicit op assignment
2. Ask Claude to implement the op and run local validation
3. Ask Codex to review the resulting patch
4. Feed Codex review back into Claude until review passes or the run escalates
5. Commit, push, open/update a PR against `shaninja/onnx2keras`
6. Poll CI, feed CI failures back into Claude, and repeat review if needed

The first implementation handles one op at a time. The design must still support later growth into a multi-op manager with prioritization and concurrency.

## Primary Goals

- Script repetitive orchestration instead of relying on agents for workflow bookkeeping
- Keep agents non-interactive and deterministic
- Persist enough state to resume cleanly after crashes or interruptions
- Enforce repository safety rules in code, especially fork/remote/PR targeting
- Keep the design extensible to future multi-run scheduling
- Document both the v1 behavior and the future roadmap inside the repo

## Non-Goals For V1

- Automatic discovery or prioritization of which op to implement
- Multiple concurrent op runs
- Direct GitHub API integration
- Automatic issue creation
- Free-form parsing of agent prose
- Human-in-the-loop prompts during normal execution

## Source Of Truth

The repository itself is the source of truth for this workflow.

V1 must document:

- the manager entrypoints and CLI usage
- the manager state machine and retry policy
- the Claude and Codex JSON contracts
- the run directory layout and artifact formats
- the PR/CI safety rules
- the future roadmap for multi-op scheduling

The initial design is captured in this file. The v1 implementation should also add repo-local operational documentation near the automation code, for example:

- `automation/README.md` for usage and workflow
- JSON schema examples under `automation/contracts/` or `automation/examples/`
- inline docstrings for state transitions and failure handling

## Repository Constraints

- `origin` is the user fork: `shaninja/onnx2keras`
- `upstream` is `tensorleap/onnx2keras`
- PRs must target the fork, never upstream
- Public CI runs with `RUN_PRIVATE_TESTS=0`
- The manager owns branch state, commits, pushes, PR creation, and CI polling
- Claude owns code changes and local test execution inside an assigned worktree
- Codex owns review and emits a structured verdict

## High-Level Architecture

### Components

1. `manager`
   - Python CLI application
   - Owns run lifecycle, persistence, retries, and remote safety

2. `Claude worker`
   - Invoked by the manager against one prepared worktree
   - Makes code changes
   - Runs local validation
   - Emits a structured result JSON

3. `Codex reviewer`
   - Invoked by the manager against the same worktree
   - Reviews the patch
   - Emits a structured review JSON including a remediation prompt when needed

4. `gh/git subprocess layer`
   - Used only by the manager
   - Handles branch/worktree setup, commit, push, PR operations, and CI polling

### Ownership Split

Manager responsibilities:

- create or restore a run
- create and manage worktrees and branches
- invoke Claude and Codex in non-interactive mode
- validate and route JSON artifacts
- enforce retry caps and escalation
- create commits
- push and open/update PRs
- poll CI and persist CI artifacts

Claude responsibilities:

- implement the assigned op in the provided worktree
- run required local validation
- summarize the implementation status in JSON

Codex responsibilities:

- review the patch in the provided worktree
- classify findings by severity
- provide a structured verdict and a remediation prompt for Claude

## Execution Model

The first version is a local Python CLI, not another manager agent.

Example commands:

- `python -m automation.manager start --op CastLike`
- `python -m automation.manager resume --run-id 20260417-103000-castlike`
- `python -m automation.manager status --run-id 20260417-103000-castlike`

The manager receives one explicit assignment from the user. It does not select the op on its own in v1.

## State Machine

The manager persists an explicit state machine:

`INIT -> PREPARE_WORKTREE -> CLAUDE_IMPLEMENT -> CODEX_REVIEW -> CLAUDE_FIX_LOOP -> READY_TO_COMMIT -> COMMIT -> PUSH -> OPEN_OR_UPDATE_PR -> POLL_CI -> CI_FIX_LOOP -> DONE | ESCALATED`

### State Intent

- `INIT`
  - create run metadata
- `PREPARE_WORKTREE`
  - ensure clean base state
  - create or restore branch/worktree for the assigned op
- `CLAUDE_IMPLEMENT`
  - invoke Claude for the first implementation pass
- `CODEX_REVIEW`
  - invoke Codex review on the current worktree diff
- `CLAUDE_FIX_LOOP`
  - invoke Claude with Codex remediation payload until approved or review cap reached
- `READY_TO_COMMIT`
  - verify manager policy says the run may move forward
- `COMMIT`
  - create a manager-owned commit with a standardized message
- `PUSH`
  - push the branch to `origin`
- `OPEN_OR_UPDATE_PR`
  - create or reuse a PR on `shaninja/onnx2keras`
- `POLL_CI`
  - collect CI status and logs through `gh`
- `CI_FIX_LOOP`
  - feed CI failures into Claude, re-run review, then retry push/CI until pass or cap reached
- `DONE`
  - run completed successfully
- `ESCALATED`
  - run stopped and requires human intervention

## Run Directory Layout

Each assignment gets a durable run directory:

`automation/runs/<timestamp>-<op>/`

Suggested contents:

- `run.json`
  - canonical run metadata and current state
- `inputs/assignment.json`
  - normalized user assignment
- `artifacts/claude/round-<n>/`
  - prompts, stdout/stderr, result JSON
- `artifacts/codex/review-<n>/`
  - prompts, stdout/stderr, result JSON
- `artifacts/ci/attempt-<n>/`
  - check summaries, failing jobs, log excerpts
- `logs/manager.log`
  - manager actions and transition log

The manager should append round-specific artifacts instead of overwriting prior results.

## Agent Invocation Rules

- Agents must run non-interactively
- Agents should receive all required permissions up front
- If an agent asks for user input or stalls on permissions, the manager treats the run as failed
- The manager must prefer deterministic scripting for setup, cleanup, commit, push, PR, and CI steps
- Agent prompts should reference file paths and artifact paths directly

## Claude Contract

Claude writes a final JSON file at a manager-provided path.

Required fields:

```json
{
  "status": "needs_review",
  "summary": "Implemented CastLike converter and added dtype coverage tests.",
  "tests_run": [
    "PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python poetry run python -m pytest test/layers/operations/test_cast_like.py -v"
  ],
  "tests_passed": true,
  "files_changed": [
    "onnx2kerastl/operation_layers.py",
    "onnx2kerastl/layers.py",
    "test/layers/operations/test_cast_like.py"
  ],
  "notes_for_reviewer": "Used existing cast helper pattern for same-dtype symbolic tensors.",
  "blocking_reason": null
}
```

Allowed Claude statuses:

- `needs_review`
- `blocked`
- `failed`

Policy:

- Claude may emit `needs_review` only when required local validation has passed
- If local tests fail, Claude must return `blocked` or `failed`
- Claude may include extra debug logs, but the manager trusts only the final JSON

## Codex Contract

Codex writes a final JSON file at a manager-provided path.

Required fields:

```json
{
  "status": "changes_requested",
  "summary": "Converter mostly matches local patterns but misses one dynamic dtype path.",
  "findings": [
    {
      "id": "correctness-castlike-001",
      "severity": "medium",
      "category": "correctness",
      "title": "Dynamic tensor path skips dtype normalization",
      "detail": "One branch leaves symbolic tensors on the old dtype.",
      "file": "onnx2kerastl/operation_layers.py",
      "line": 123,
      "must_fix": true,
      "suggested_fix": "Normalize both constant and symbolic paths through the same dtype helper."
    }
  ],
  "prompt_for_claude": "Address the medium-severity finding in onnx2kerastl/operation_layers.py by normalizing the symbolic tensor path through the same dtype handling used for constants. Re-run the relevant pytest target and update your structured result.",
  "ready_to_push": false
}
```

Allowed Codex statuses:

- `approved`
- `approved_with_notes`
- `changes_requested`
- `blocked`

## Review Policy

The manager applies review policy. Claude does not decide whether to ignore findings.

### Finding Severities

- `nit`
- `low`
- `medium`
- `high`
- `blocker`

### Verdict Rules

- `approved`
  - zero findings remain
- `approved_with_notes`
  - only `nit` or `low` findings remain
- `changes_requested`
  - any `medium`, `high`, or `blocker` finding remains
  - or any finding has `must_fix: true`
- `blocked`
  - review could not complete reliably

### Manager Policy

- `approved` -> proceed to commit/push/PR
- `approved_with_notes` -> proceed, but preserve notes in artifacts and optionally PR body
- `changes_requested` -> route `prompt_for_claude` into the next Claude round
- `blocked` -> escalate

## Retry And Escalation Policy

Initial caps:

- maximum 7 Codex review rounds
- maximum 3 CI remediation rounds

Escalate when:

- review cap is reached
- CI remediation cap is reached
- agent output JSON is missing or invalid
- an agent becomes interactive or stalls
- remote safety validation fails
- PR creation target is ambiguous
- the worktree cannot be restored or reconciled

Escalation should preserve the final reason and all artifacts in the run directory.

## Commit Policy

The manager creates commits. Claude does not commit or push.

Reasons:

- one authority owns branch state
- standardized commit messages are easier to enforce
- avoids partial staging, wrong remote pushes, and branch drift

The manager should inspect the working tree before committing and refuse to commit if review policy has not passed.

## Remote Safety Rules

These rules must be enforced in code:

- verify `origin` maps to `shaninja/onnx2keras`
- never open a PR against `tensorleap/onnx2keras`
- pass explicit repository, base, and head arguments to `gh`
- fail closed if repo identity cannot be proven
- reuse an existing PR for the branch when resuming

## CI Loop

After push and PR creation, the manager polls CI through `gh`.

CI states:

- `pending`
- `passed`
- `failed`

On failure, the manager should:

1. store raw CI data and useful excerpts in the run artifacts
2. classify the failure into a deterministic remediation payload
3. send that payload to Claude as a CI-fix round
4. run Codex review again after Claude changes
5. re-push and poll CI again if review passes

CI feedback should reuse the same Claude/Codex loop instead of creating a separate review protocol.

## Local Validation Expectations

Claude should not hand off to review until it has run local validation appropriate to the change.

For this repo, the manager prompt should remind Claude of:

- relevant targeted pytest commands for the changed op
- public-CI expectations, especially that private tests are not available in normal fork CI
- the existing Makefile and poetry-based commands already used by the repo

The manager may also run cheap guard checks before commit, but Claude remains responsible for implementation-time testing.

## Error Handling

The manager should fail fast on:

- missing worktree
- missing or invalid JSON artifacts
- non-zero subprocess exit without a recognized recoverable path
- interactive prompts
- wrong remote or PR target
- inability to determine CI state

Recoverable errors should transition to `ESCALATED`, not silently retry forever.

## Testing Strategy For The Manager

The manager itself should be tested with scripted fixtures and mocked subprocess responses.

At minimum:

- state transition tests
- JSON validation tests
- resume behavior tests
- remote safety tests
- retry-cap enforcement tests
- PR reuse logic tests
- CI failure classification tests

Where practical, sample Claude/Codex JSON fixtures should live in the repo as contract examples.

## Future Roadmap

### Phase 2

- allow the manager to take assignments from a prioritized queue instead of only direct user input
- add a worktree pool and multiple concurrent runs
- keep per-run isolation so the current v1 contracts remain valid

### Phase 3

- smarter scheduling to reduce merge conflicts between op branches
- reviewer pooling or shared Codex review workers if this helps throughput
- automatic issue creation for escalated runs
- richer CI analysis and remediation classification

### Phase 4

- optional API-driven integrations if CLI orchestration becomes a bottleneck
- dashboards or summaries over all active runs
- automatic branch cleanup and merge follow-up workflows

## Recommended V1 File Layout

One reasonable implementation shape:

```text
automation/
  README.md
  manager.py
  state_machine.py
  contracts/
    claude_result.schema.json
    codex_review.schema.json
  prompts/
    claude_implement.md
    codex_review.md
  runs/
    .gitkeep
```

This is a recommendation, not a hard requirement, but v1 should keep code, contracts, and operational docs together in the repo.

## Decision Summary

- Use a Python CLI manager for orchestration
- Start with one explicit op assignment at a time
- Keep manager ownership over `git`, `gh`, commits, push, PR, and CI polling
- Keep Claude responsible for code changes and local validation
- Keep Codex responsible for structured review and remediation prompts
- Require JSON-only final artifacts at the manager boundary
- Persist every run and every round to disk for resume and auditability
- Design for future multi-op scheduling without implementing it in v1
