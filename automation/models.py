from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class ManagerState(str, Enum):
    INIT = "INIT"
    PREPARE_WORKTREE = "PREPARE_WORKTREE"
    CLAUDE_IMPLEMENT = "CLAUDE_IMPLEMENT"
    CODEX_REVIEW = "CODEX_REVIEW"
    CLAUDE_FIX_LOOP = "CLAUDE_FIX_LOOP"
    READY_TO_COMMIT = "READY_TO_COMMIT"
    COMMIT = "COMMIT"
    PUSH = "PUSH"
    OPEN_OR_UPDATE_PR = "OPEN_OR_UPDATE_PR"
    POLL_CI = "POLL_CI"
    CI_FIX_LOOP = "CI_FIX_LOOP"
    DONE = "DONE"
    ESCALATED = "ESCALATED"


@dataclass
class RunRecord:
    run_id: str
    op_name: str
    branch_name: str
    state: ManagerState
    repo_root: Path
    run_dir: Path
    run_file: Path
    review_round: int = 0
    ci_round: int = 0
    worktree_path: Optional[Path] = None
    pr_number: Optional[int] = None
    last_error: Optional[str] = None
