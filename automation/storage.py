import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from automation.models import ManagerState, RunRecord


def _slugify_op_name(op_name: str) -> str:
    return op_name.strip().lower().replace("_", "-")


def _serialize_record(record: RunRecord) -> Dict[str, Any]:
    payload = asdict(record)
    for key in ("repo_root", "run_dir", "run_file", "worktree_path"):
        value = payload[key]
        payload[key] = None if value is None else str(value)
    payload["state"] = record.state.value
    return payload


def _deserialize_record(payload: Dict[str, Any]) -> RunRecord:
    worktree_path = payload.get("worktree_path")
    return RunRecord(
        run_id=payload["run_id"],
        op_name=payload["op_name"],
        branch_name=payload["branch_name"],
        state=ManagerState(payload["state"]),
        repo_root=Path(payload["repo_root"]),
        run_dir=Path(payload["run_dir"]),
        run_file=Path(payload["run_file"]),
        review_round=payload.get("review_round", 0),
        ci_round=payload.get("ci_round", 0),
        worktree_path=None if worktree_path is None else Path(worktree_path),
        pr_number=payload.get("pr_number"),
        last_error=payload.get("last_error"),
    )


def save_run_record(record: RunRecord) -> None:
    record.run_file.write_text(
        json.dumps(_serialize_record(record), indent=2, sort_keys=True) + "\n"
    )


def load_run_record(run_file: Path) -> RunRecord:
    return _deserialize_record(json.loads(run_file.read_text()))


def create_run_record(runs_root: Path, repo_root: Path, op_name: str) -> RunRecord:
    slug = _slugify_op_name(op_name)
    run_id = f"{datetime.utcnow():%Y%m%d-%H%M%S}-{slug}"
    run_dir = runs_root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    for relative_path in (
        "inputs",
        "artifacts",
        "artifacts/claude",
        "artifacts/codex",
        "artifacts/ci",
        "logs",
    ):
        (run_dir / relative_path).mkdir(parents=True, exist_ok=True)

    run_file = run_dir / "run.json"
    record = RunRecord(
        run_id=run_id,
        op_name=op_name,
        branch_name=f"add/{slug}",
        state=ManagerState.INIT,
        repo_root=repo_root,
        run_dir=run_dir,
        run_file=run_file,
    )
    save_run_record(record)
    return record
