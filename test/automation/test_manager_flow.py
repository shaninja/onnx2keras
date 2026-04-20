import json
from pathlib import Path

from automation.manager import main, run_start


def test_main_status_emits_json_for_existing_run(tmp_path: Path, capsys):
    run = run_start(runs_root=tmp_path, repo_root=tmp_path, op_name="CastLike")

    exit_code = main(["status", "--run-file", str(run.run_file)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["state"] == "PREPARE_WORKTREE"
    assert payload["branch_name"] == "add/castlike"
