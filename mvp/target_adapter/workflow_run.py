"""Bounded production effect runner for the reusable target workflow."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
from typing import Any

import requests

from .contract import ExecutionRequest
from .ownership import (
    ManagedPullRequest,
    branch_name,
    marker,
    reconcile,
    OwnershipState,
)
from .result import build_result, safe_message, validate_result


def _request(payload: dict[str, Any], admitted: dict[str, Any]) -> ExecutionRequest:
    task, source = payload["task"], payload["source"]
    return ExecutionRequest(
        payload,
        admitted["delivery_id"],
        payload["correlation_id"],
        task["id"],
        task["type"],
        task["instructions"],
        admitted["mode"],
        source["repository"],
        source["issue_number"],
        admitted["payload_digest"],
    )


def _run(
    command: list[str], *, env: dict[str, str] | None = None, timeout: int = 900
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command, text=True, capture_output=True, env=env, timeout=timeout, check=False
    )
    if completed.returncode:
        raise RuntimeError(
            f"{command[0]} failed ({completed.returncode}): {safe_message(completed.stderr)}"
        )
    return completed


def _prs(token: str) -> list[ManagedPullRequest]:
    env = {"PATH": os.environ["PATH"], "GH_TOKEN": token}
    data = json.loads(
        _run(
            [
                "gh",
                "pr",
                "list",
                "--repo",
                "Young-Consultations/slugger",
                "--state",
                "all",
                "--json",
                "number,url,state,isDraft,headRefName,baseRefName,body",
                "--limit",
                "100",
            ],
            env=env,
            timeout=60,
        ).stdout
    )
    return [
        ManagedPullRequest(
            item["number"],
            item["url"],
            item["state"],
            item["isDraft"],
            item["headRefName"],
            item["baseRefName"],
            item["body"],
        )
        for item in data
    ]


def _branch_exists(branch: str, token: str) -> bool:
    env = {"PATH": os.environ["PATH"], "GH_TOKEN": token}
    result = subprocess.run(
        ["gh", "api", f"repos/Young-Consultations/slugger/git/ref/heads/{branch}"],
        text=True,
        capture_output=True,
        env=env,
        timeout=60,
        check=False,
    )
    return result.returncode == 0


def _codex(request: ExecutionRequest) -> None:
    key = os.environ["CODEX_API_KEY"]
    env = {
        "HOME": os.environ.get("HOME", ""),
        "PATH": os.environ["PATH"],
        "CODEX_API_KEY": key,
    }
    prompt = (
        "Modify only this Slugger repository for the admitted task. Do not expose secrets, alter approval, merge, release, or deploy authority. Task:\n"
        + request.instructions
    )
    _run(
        ["codex", "exec", "--sandbox", "workspace-write", prompt],
        env=env,
        timeout=900,
    )


def _validate_candidate_policy() -> None:
    status = _run(["git", "status", "--porcelain=v1", "-z"]).stdout
    changed = []
    for record in status.split("\0"):
        if not record:
            continue
        relative = record[3:]
        if " -> " in relative:
            relative = relative.rsplit(" -> ", 1)[1]
        changed.append(relative)
    if not changed:
        raise RuntimeError("candidate produced no changes")
    protected = (".github/", "AI_CONTEXT.md", "SECURITY.md", "mvp/target_adapter/")
    for relative in changed:
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or relative.startswith(protected):
            raise RuntimeError(f"candidate modified protected path: {relative}")
        if path.is_symlink():
            raise RuntimeError(f"candidate created a symbolic link: {relative}")


def _validate() -> None:
    _validate_candidate_policy()
    env = {
        "HOME": os.environ.get("HOME", ""),
        "PATH": os.environ["PATH"],
        "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
    }
    for command in (
        ["ruff", "check", "."],
        ["ruff", "format", "--check", "."],
        ["python", "-m", "mypy", "mvp", "cli"],
        ["python", "-m", "pytest", "tests/", "-q"],
        ["python", "-m", "build"],
    ):
        _run(list(command), env=env, timeout=600)
    _run(["git", "diff", "--check"], env=env, timeout=60)


def _publish(request: ExecutionRequest, branch: str, token: str) -> ManagedPullRequest:
    env = {
        "HOME": os.environ.get("HOME", ""),
        "PATH": os.environ["PATH"],
        "GH_TOKEN": token,
    }
    _run(["git", "config", "user.name", "slugger-target-adapter"], env=env)
    _run(
        [
            "git",
            "config",
            "user.email",
            "slugger-target-adapter@users.noreply.github.com",
        ],
        env=env,
    )
    _run(["git", "checkout", "-b", branch], env=env)
    _run(["git", "add", "--all"], env=env)
    status = _run(["git", "status", "--porcelain"], env=env).stdout
    if not status.strip():
        raise RuntimeError("candidate produced no changes")
    _run(["git", "commit", "-m", f"Implement admitted task {request.task_id}"], env=env)
    remote = (
        f"https://x-access-token:{token}@github.com/Young-Consultations/slugger.git"
    )
    _run(["git", "push", remote, f"HEAD:refs/heads/{branch}"], env=env, timeout=120)
    body = (
        marker(request)
        + "\n\nGenerated by the Slugger canonical target adapter. Human review is required."
    )
    try:
        url = _run(
            [
                "gh",
                "pr",
                "create",
                "--repo",
                "Young-Consultations/slugger",
                "--draft",
                "--base",
                "main",
                "--head",
                branch,
                "--title",
                f"Implement {request.task_id}",
                "--body",
                body,
            ],
            env=env,
            timeout=120,
        ).stdout.strip()
    except RuntimeError:
        decision = reconcile(request, _prs(token), branch_exists=True)
        if decision.state is OwnershipState.REUSE and decision.pull_request:
            return decision.pull_request
        raise
    number = int(url.rstrip("/").rsplit("/", 1)[-1])
    return ManagedPullRequest(number, url, "OPEN", True, branch, "main", body)


def _validate_canonical_result(result: dict[str, Any]) -> None:
    url = "https://raw.githubusercontent.com/Young-Consultations/.github/c6090e5bbadcc2102a1cb91875466e9decdada1e/contracts/execution-result.schema.json"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    schema = response.json()
    if not isinstance(schema, dict):
        raise RuntimeError("canonical result schema is not an object")
    validate_result(result, schema)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--input", required=True)
    parser.add_argument("--admission", required=True)
    parser.add_argument("--github-output", required=True)
    args = parser.parse_args(argv)
    payload = json.loads(Path(args.input).read_text())
    admitted = json.loads(Path(args.admission).read_text())
    request = _request(payload, admitted)
    if args.verify_only:
        result = build_result(request, "verified", summary="request verified")
        _validate_canonical_result(result)
        source = f"{request.source_repository}#{request.source_issue}"
        with Path(args.github_output).open("a", encoding="utf-8") as output:
            output.write(
                "execution_result=" + json.dumps(result, separators=(",", ":")) + "\n"
            )
            output.write("source_issue=" + source + "\n")
        return 0
    token = os.environ["SLUGGER_PUBLICATION_TOKEN"]
    try:
        decision = reconcile(
            request,
            _prs(token),
            branch_exists=_branch_exists(branch_name(request.delivery_id), token),
        )
        if decision.state is OwnershipState.AMBIGUOUS:
            result = build_result(
                request, "failed", summary=decision.reason, failure_category="ownership"
            )
        elif decision.state is OwnershipState.REUSE:
            assert decision.pull_request
            result = build_result(
                request,
                "duplicate-reused",
                summary="managed draft reused",
                branch=decision.branch,
                pull_request_url=decision.pull_request.url,
            )
        elif request.mode == "verify":
            result = build_result(request, "verified", summary="request verified")
        else:
            _codex(request)
            _validate()
            pr = _publish(request, decision.branch, token)
            result = build_result(
                request,
                "succeeded",
                summary="validated draft created",
                branch=decision.branch,
                pull_request_url=pr.url,
            )
    except subprocess.TimeoutExpired as exc:
        result = build_result(
            request,
            "failed",
            summary=f"execution timed out: {exc.cmd[0]}",
            failure_category="timeout",
        )
    except Exception as exc:
        result = build_result(
            request, "failed", summary=str(exc), failure_category="execution"
        )
    _validate_canonical_result(result)
    source = f"{request.source_repository}#{request.source_issue}"
    with Path(args.github_output).open("a", encoding="utf-8") as output:
        output.write(
            "execution_result=" + json.dumps(result, separators=(",", ":")) + "\n"
        )
        output.write("source_issue=" + source + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
