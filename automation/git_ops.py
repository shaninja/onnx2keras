EXPECTED_FORK = "shaninja/onnx2keras"
EXPECTED_UPSTREAM = "tensorleap/onnx2keras"


def ensure_origin_is_fork(remote_url: str) -> None:
    normalized = remote_url.strip().replace(".git", "")
    if EXPECTED_FORK not in normalized:
        raise ValueError(f"origin must point to {EXPECTED_FORK}, got {remote_url}")


def format_pr_create_args(branch_name: str, title: str, body: str = "") -> list:
    args = [
        "gh",
        "pr",
        "create",
        f"--repo={EXPECTED_FORK}",
        "--base=master",
        f"--head=shaninja:{branch_name}",
        f"--title={title}",
    ]
    if body:
        args.append(f"--body={body}")
    return args
