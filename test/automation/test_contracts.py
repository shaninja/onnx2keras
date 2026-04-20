from automation.agent_contracts import parse_claude_result, parse_codex_review


def test_parse_claude_result_requires_tests_for_needs_review():
    payload = {
        "status": "needs_review",
        "summary": "done",
        "tests_run": [],
        "tests_passed": False,
        "files_changed": ["onnx2kerastl/layers.py"],
        "notes_for_reviewer": "note",
        "blocking_reason": None,
    }

    try:
        parse_claude_result(payload)
    except ValueError as exc:
        assert "tests_passed" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_parse_codex_review_requires_prompt_when_changes_requested():
    payload = {
        "status": "changes_requested",
        "summary": "needs fixes",
        "findings": [],
        "prompt_for_claude": "",
        "ready_to_push": False,
    }

    try:
        parse_codex_review(payload)
    except ValueError as exc:
        assert "prompt_for_claude" in str(exc)
    else:
        raise AssertionError("expected ValueError")
