from automation.git_ops import ensure_origin_is_fork, format_pr_create_args


def test_ensure_origin_is_fork_accepts_shaninja_ssh():
    ensure_origin_is_fork("git@github.com:shaninja/onnx2keras.git")


def test_ensure_origin_is_fork_rejects_upstream():
    try:
        ensure_origin_is_fork("git@github.com:tensorleap/onnx2keras.git")
    except ValueError as exc:
        assert "shaninja/onnx2keras" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_format_pr_create_args_is_explicit():
    args = format_pr_create_args(branch_name="add/castlike", title="Add CastLike support")

    assert "--repo=shaninja/onnx2keras" in args
    assert "--base=master" in args
    assert "--head=shaninja:add/castlike" in args
