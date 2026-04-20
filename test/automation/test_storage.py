from pathlib import Path

from automation.models import ManagerState
from automation.storage import create_run_record, load_run_record, save_run_record


def test_create_run_record_uses_slugged_op_and_initial_state(tmp_path: Path):
    record = create_run_record(tmp_path, repo_root=tmp_path, op_name="CastLike")

    assert record.op_name == "CastLike"
    assert record.branch_name == "add/castlike"
    assert record.state is ManagerState.INIT
    assert record.run_dir.exists()
    assert record.run_file.exists()


def test_save_and_load_run_record_round_trip(tmp_path: Path):
    record = create_run_record(tmp_path, repo_root=tmp_path, op_name="Softmax")
    record.review_round = 2
    save_run_record(record)

    loaded = load_run_record(record.run_file)

    assert loaded.run_id == record.run_id
    assert loaded.state is ManagerState.INIT
    assert loaded.review_round == 2
