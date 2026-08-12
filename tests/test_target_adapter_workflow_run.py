from dataclasses import replace
import json
import subprocess

import pytest

from mvp.target_adapter.ownership import ManagedPullRequest, branch_name, marker
from mvp.target_adapter import workflow_run
from tests.test_target_adapter_execution import request
from tests.test_target_adapter_contract import payload


def test_candidate_policy_checks_rename_source(tmp_path, monkeypatch):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    protected = tmp_path / ".github" / "workflows"
    protected.mkdir(parents=True)
    (protected / "ci.yml").write_text("name: CI\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-qm",
            "initial",
        ],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "mv", ".github/workflows/ci.yml", "unprotected.yml"],
        cwd=tmp_path,
        check=True,
    )
    monkeypatch.chdir(tmp_path)

    with pytest.raises(RuntimeError, match=r"\.github/workflows/ci.yml"):
        workflow_run._validate_candidate_policy()


def test_publish_pushes_with_create_only_lease(monkeypatch):
    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)
        stdout = "changes\n" if command[:3] == ["git", "status", "--porcelain"] else ""
        if command[:3] == ["gh", "pr", "create"]:
            stdout = "https://github.com/Young-Consultations/slugger/pull/1\n"
        return subprocess.CompletedProcess(command, 0, stdout, "")

    monkeypatch.setattr(workflow_run, "_run", fake_run)
    admitted = request()
    branch = branch_name(admitted.delivery_id)
    workflow_run._publish(admitted, branch, "token")

    push = next(command for command in commands if command[:2] == ["git", "push"])
    assert f"--force-with-lease=refs/heads/{branch}:" in push


def test_verify_reconciles_conflicting_delivery(tmp_path, monkeypatch):
    value = payload()
    value["mode"] = "verify"
    admitted = request("verify")
    admission = {
        "delivery_id": admitted.delivery_id,
        "mode": admitted.mode,
        "payload_digest": admitted.payload_digest,
    }
    input_path = tmp_path / "input.json"
    admission_path = tmp_path / "admission.json"
    output_path = tmp_path / "output"
    input_path.write_text(json.dumps(value))
    admission_path.write_text(json.dumps(admission))
    conflicting = replace(admitted, payload_digest="conflicting-digest")
    branch = branch_name(admitted.delivery_id)
    pr = ManagedPullRequest(
        1, "https://example/pr/1", "OPEN", True, branch, "main", marker(conflicting)
    )
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setattr(workflow_run, "_prs", lambda token: [pr])
    monkeypatch.setattr(workflow_run, "_branch_exists", lambda name, token: True)
    monkeypatch.setattr(workflow_run, "_validate_canonical_result", lambda result: None)

    assert (
        workflow_run.main(
            [
                "--verify-only",
                "--input",
                str(input_path),
                "--admission",
                str(admission_path),
                "--github-output",
                str(output_path),
            ]
        )
        == 0
    )
    result = json.loads(output_path.read_text().splitlines()[0].split("=", 1)[1])
    assert result["execution_status"] == "failed"
    assert result["failure_category"] == "ownership"
