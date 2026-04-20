# Op Manager V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repo-local Python CLI manager that can initialize and persist one op-manager run, validate Claude/Codex JSON contracts, and enforce fork-safe GitHub operations for future automation loops.

**Architecture:** Add a focused `automation/` package for state models, persistence, contract parsing, and git/GitHub safety helpers, then expose a small CLI in `automation/manager.py`. Cover the package with pytest tests and document the current v1 behavior plus future roadmap in repo-local docs.

**Tech Stack:** Python 3.8+, `argparse`, `dataclasses`, `json`, `pathlib`, `subprocess`, `pytest`

---

### Task 1: Create Run-State Models And Persistence

**Files:**
- Create: `automation/__init__.py`
- Create: `automation/models.py`
- Create: `automation/storage.py`
- Create: `automation/runs/.gitkeep`
- Test: `test/automation/test_storage.py`

- [ ] **Step 1: Write the failing storage tests**
- [ ] **Step 2: Run `pytest -q test/automation/test_storage.py` and verify the import failure**
- [ ] **Step 3: Implement `ManagerState`, `RunRecord`, and storage helpers to create/load/save run metadata**
- [ ] **Step 4: Re-run `pytest -q test/automation/test_storage.py` and verify it passes**
- [ ] **Step 5: Commit the storage primitives**

### Task 2: Add Agent Contract Parsing

**Files:**
- Modify: `automation/models.py`
- Create: `automation/contracts.py`
- Create: `automation/contracts/claude_result.schema.json`
- Create: `automation/contracts/codex_review.schema.json`
- Test: `test/automation/test_contracts.py`

- [ ] **Step 1: Write the failing contract tests**
- [ ] **Step 2: Run `pytest -q test/automation/test_contracts.py` and verify the parser import failure**
- [ ] **Step 3: Implement Claude/Codex result dataclasses plus validation rules**
- [ ] **Step 4: Re-run `pytest -q test/automation/test_contracts.py` and verify it passes**
- [ ] **Step 5: Commit the contract layer**

### Task 3: Add Remote Safety Helpers

**Files:**
- Create: `automation/git_ops.py`
- Test: `test/automation/test_git_ops.py`

- [ ] **Step 1: Write the failing git-helper tests**
- [ ] **Step 2: Run `pytest -q test/automation/test_git_ops.py` and verify the helper import failure**
- [ ] **Step 3: Implement fork validation and explicit PR argument formatting**
- [ ] **Step 4: Re-run `pytest -q test/automation/test_git_ops.py` and verify it passes**
- [ ] **Step 5: Commit the git/GitHub safety layer**

### Task 4: Add Manager CLI Commands

**Files:**
- Create: `automation/manager.py`
- Modify: `automation/storage.py`
- Test: `test/automation/test_manager.py`

- [ ] **Step 1: Write the failing manager tests**
- [ ] **Step 2: Run `pytest -q test/automation/test_manager.py` and verify the CLI helper failure**
- [ ] **Step 3: Implement `start`, `status`, and `resume` command plumbing over persisted run state**
- [ ] **Step 4: Re-run `pytest -q test/automation/test_manager.py` and verify it passes**
- [ ] **Step 5: Commit the manager CLI**

### Task 5: Document The Repo-Local Workflow

**Files:**
- Create: `automation/README.md`
- Modify: `.gitignore`
- Test: `test/automation/test_manager_flow.py`

- [ ] **Step 1: Write the failing status-flow test**
- [ ] **Step 2: Run `pytest -q test/automation/test_manager_flow.py` and verify the failure**
- [ ] **Step 3: Implement any missing status helpers, ignore `automation/runs/`, and document current behavior plus future plans**
- [ ] **Step 4: Run `pytest -q test/automation` and verify the full automation test suite passes**
- [ ] **Step 5: Commit the docs and final manager polish**

## Self-Review

- Spec coverage: the tasks cover persisted runs, JSON contracts, manager CLI entrypoints, remote safety, and repo-local documentation for both current behavior and future plans.
- Placeholder scan: no `TODO`, `TBD`, or hand-wavy “implement later” steps remain.
- Type consistency: the plan consistently uses `RunRecord`, `ManagerState`, `ClaudeResult`, `CodexReview`, and `automation/manager.py`.

Plan complete and saved to `docs/superpowers/plans/2026-04-17-op-manager-v1.md`. The user explicitly asked to proceed, so execution should continue inline using `executing-plans`.
