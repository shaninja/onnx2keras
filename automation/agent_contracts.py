from dataclasses import dataclass
from typing import Any, Dict, List, Optional


VALID_CLAUDE_STATUSES = {"needs_review", "blocked", "failed"}
VALID_REVIEW_STATUSES = {
    "approved",
    "approved_with_notes",
    "changes_requested",
    "blocked",
}
VALID_SEVERITIES = {"nit", "low", "medium", "high", "blocker"}


@dataclass
class ClaudeResult:
    status: str
    summary: str
    tests_run: List[str]
    tests_passed: bool
    files_changed: List[str]
    notes_for_reviewer: str
    blocking_reason: Optional[str]


@dataclass
class ReviewFinding:
    id: str
    severity: str
    category: str
    title: str
    detail: str
    file: str
    line: int
    must_fix: bool
    suggested_fix: str


@dataclass
class CodexReview:
    status: str
    summary: str
    findings: List[ReviewFinding]
    prompt_for_claude: str
    ready_to_push: bool


def parse_claude_result(payload: Dict[str, Any]) -> ClaudeResult:
    status = payload["status"]
    if status not in VALID_CLAUDE_STATUSES:
        raise ValueError(f"unsupported Claude status: {status}")

    if status == "needs_review" and not payload["tests_passed"]:
        raise ValueError("needs_review requires tests_passed=true")

    if status == "needs_review" and not payload["tests_run"]:
        raise ValueError("needs_review requires tests_run")

    return ClaudeResult(
        status=status,
        summary=payload["summary"],
        tests_run=list(payload["tests_run"]),
        tests_passed=bool(payload["tests_passed"]),
        files_changed=list(payload["files_changed"]),
        notes_for_reviewer=payload.get("notes_for_reviewer", ""),
        blocking_reason=payload.get("blocking_reason"),
    )


def parse_codex_review(payload: Dict[str, Any]) -> CodexReview:
    status = payload["status"]
    if status not in VALID_REVIEW_STATUSES:
        raise ValueError(f"unsupported Codex review status: {status}")

    prompt_for_claude = payload.get("prompt_for_claude", "")
    if status == "changes_requested" and not prompt_for_claude.strip():
        raise ValueError("changes_requested requires prompt_for_claude")

    findings = []
    for raw_finding in payload.get("findings", []):
        severity = raw_finding["severity"]
        if severity not in VALID_SEVERITIES:
            raise ValueError(f"unsupported finding severity: {severity}")
        findings.append(ReviewFinding(**raw_finding))

    return CodexReview(
        status=status,
        summary=payload["summary"],
        findings=findings,
        prompt_for_claude=prompt_for_claude,
        ready_to_push=bool(payload["ready_to_push"]),
    )
