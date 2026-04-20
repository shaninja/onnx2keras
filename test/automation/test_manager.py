from pathlib import Path

from automation.manager import build_parser, run_resume, run_start, run_status


def test_build_parser_accepts_start_command():
    parser = build_parser()
    args = parser.parse_args(["start", "--op", "CastLike"])

    assert args.command == "start"
    assert args.op == "CastLike"


def test_run_start_creates_run_and_advances_to_prepare(tmp_path: Path):
    run = run_start(runs_root=tmp_path, repo_root=tmp_path, op_name="CastLike")

    assert run.op_name == "CastLike"
    assert run.state.value == "PREPARE_WORKTREE"


def test_run_status_and_resume_read_the_same_run(tmp_path: Path):
    run = run_start(runs_root=tmp_path, repo_root=tmp_path, op_name="Softmax")

    status = run_status(run.run_file)
    resumed = run_resume(run.run_file)

    assert status["branch_name"] == "add/softmax"
    assert status["state"] == "PREPARE_WORKTREE"
    assert resumed.run_id == run.run_id
