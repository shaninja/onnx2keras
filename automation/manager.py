import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional

from automation.models import ManagerState, RunRecord
from automation.storage import create_run_record, load_run_record, save_run_record


DEFAULT_RUNS_ROOT = Path("automation/runs")
DEFAULT_REPO_ROOT = Path(".")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="op-manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("--op", required=True)
    start_parser.add_argument("--runs-root", default=str(DEFAULT_RUNS_ROOT))
    start_parser.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--run-file", required=True)

    resume_parser = subparsers.add_parser("resume")
    resume_parser.add_argument("--run-file", required=True)
    return parser


def run_start(runs_root: Path, repo_root: Path, op_name: str) -> RunRecord:
    record = create_run_record(runs_root=runs_root, repo_root=repo_root, op_name=op_name)
    record.state = ManagerState.PREPARE_WORKTREE
    save_run_record(record)
    return record


def run_status(run_file: Path) -> Dict[str, Any]:
    record = load_run_record(run_file)
    return {
        "run_id": record.run_id,
        "op_name": record.op_name,
        "branch_name": record.branch_name,
        "state": record.state.value,
        "review_round": record.review_round,
        "ci_round": record.ci_round,
        "pr_number": record.pr_number,
    }


def run_resume(run_file: Path) -> RunRecord:
    return load_run_record(run_file)


def main(argv: Optional[list] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "start":
        record = run_start(
            runs_root=Path(args.runs_root),
            repo_root=Path(args.repo_root),
            op_name=args.op,
        )
        print(json.dumps(run_status(record.run_file), indent=2, sort_keys=True))
        return 0

    run_file = Path(args.run_file)
    if args.command == "status":
        print(json.dumps(run_status(run_file), indent=2, sort_keys=True))
        return 0

    if args.command == "resume":
        record = run_resume(run_file)
        print(json.dumps(run_status(record.run_file), indent=2, sort_keys=True))
        return 0

    raise ValueError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
