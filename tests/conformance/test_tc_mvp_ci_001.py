"""Hermetic execution of the pinned TC-MVP-CI-001 organization oracle."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
import pytest

from mvp.target_adapter import cli, workflow_run
from mvp.target_adapter.contract import canonical_digest
from mvp.target_adapter.ownership import ManagedPullRequest, branch_name, marker
from mvp.target_adapter.result import result_digest


FIXTURES = Path("tests/conformance/fixtures")
ORACLE = json.loads((FIXTURES / "TC-MVP-CI-001.json").read_text())
PINNED = FIXTURES / ORACLE["snapshot"]
INPUT_SCHEMA = json.loads((PINNED / "execution-input.schema.json").read_text())
RESULT_SCHEMA = json.loads((PINNED / "execution-result.schema.json").read_text())
PIN = "c6090e5bbadcc2102a1cb91875466e9decdada1e"


def case(name: str) -> dict[str, Any]:
    return deepcopy(next(item for item in ORACLE["cases"] if item["name"] == name))


def admit(tmp_path: Path, monkeypatch, fixture: dict[str, Any]) -> tuple[int, Path]:
    source = tmp_path / "input.json"
    admitted = tmp_path / "admitted.json"
    schema = tmp_path / "input-schema.json"
    source.write_text(json.dumps(fixture["input"]))
    schema.write_text(json.dumps(INPUT_SCHEMA))
    monkeypatch.setenv("CONFORMANCE_SECRET", "sk-never-print-this")
    status = cli.main(
        [
            "--input",
            str(source),
            "--schema",
            str(schema),
            "--concurrency-group",
            fixture["concurrency_group"],
            "--caller-repository",
            fixture["caller_repository"],
            "--output",
            str(admitted),
        ]
    )
    return status, admitted


class WorkflowFakes:
    """Effect-free seams around the real workflow runner."""

    def __init__(self, monkeypatch, prs: list[ManagedPullRequest] | None = None):
        self.prs = list(prs or [])
        self.branch_exists = False
        self.codex_calls = 0
        self.validation_calls = 0
        self.publish_calls = 0
        self.failure: str | None = None
        self.race_pr: ManagedPullRequest | None = None
        monkeypatch.setattr(workflow_run, "_prs", lambda unused: self.prs)
        monkeypatch.setattr(
            workflow_run,
            "_branch_exists",
            lambda unused_branch, unused_token: self.branch_exists,
        )
        monkeypatch.setattr(workflow_run, "_codex", self.codex)
        monkeypatch.setattr(workflow_run, "_validate", self.validate)
        monkeypatch.setattr(workflow_run, "_publish", self.publish)
        # This uses the vendored, pinned result validator rather than performing
        # workflow_run's production network fetch.
        monkeypatch.setattr(
            workflow_run,
            "_validate_canonical_result",
            lambda value: Draft202012Validator(
                RESULT_SCHEMA, format_checker=FormatChecker()
            ).validate(value),
        )

    def codex(self, unused) -> None:
        self.codex_calls += 1
        if self.failure == "codex":
            raise RuntimeError("codex failed sk-never-print-this")

    def validate(self) -> None:
        self.validation_calls += 1
        if self.failure in {"validation", "test"}:
            raise RuntimeError(f"{self.failure} failed sk-never-print-this")

    def publish(self, request, branch: str, unused_token: str) -> ManagedPullRequest:
        self.publish_calls += 1
        if self.failure == "publication":
            raise RuntimeError("publication failed sk-never-print-this")
        if self.race_pr:
            self.prs.append(self.race_pr)
            return self.race_pr
        pr = ManagedPullRequest(
            1,
            "https://example.invalid/pr/1",
            "OPEN",
            True,
            branch,
            "main",
            marker(request),
        )
        self.prs.append(pr)
        return pr


def run_workflow(tmp_path: Path, monkeypatch, fixture: dict[str, Any], fakes=None):
    status, admitted = admit(tmp_path, monkeypatch, fixture)
    assert status == 0
    source = tmp_path / "input.json"
    output = tmp_path / "github-output"
    monkeypatch.setenv("GITHUB_TOKEN", "fake")
    monkeypatch.setenv("SLUGGER_PUBLICATION_TOKEN", "fake")
    fakes = fakes or WorkflowFakes(monkeypatch)
    args = [
        "--input",
        str(source),
        "--admission",
        str(admitted),
        "--github-output",
        str(output),
    ]
    if fixture["input"]["mode"] == "verify":
        args.insert(0, "--verify-only")
    assert workflow_run.main(args) == 0
    values = dict(line.split("=", 1) for line in output.read_text().splitlines())
    result = json.loads(values["execution_result"])
    Draft202012Validator(RESULT_SCHEMA, format_checker=FormatChecker()).validate(result)
    return result, fakes


def owned_pr(fixture: dict[str, Any], **changes) -> ManagedPullRequest:
    payload = fixture["input"]
    admitted = {
        "delivery_id": payload["delivery_id"],
        "mode": payload["mode"],
        "payload_digest": canonical_digest(payload),
    }
    request = workflow_run._request(payload, admitted)
    values = dict(
        number=1,
        url="https://example.invalid/pr/1",
        state="OPEN",
        draft=True,
        head=branch_name(request.delivery_id),
        base="main",
        body=marker(request),
    )
    values.update(changes)
    return ManagedPullRequest(**values)


def test_oracle_is_executable_pinned_snapshot():
    assert ORACLE["organization_revision"] == PIN
    assert ORACLE["fixture_set"] == "TC-MVP-CI-001"
    assert len(ORACLE["cases"]) == 22
    assert {item["name"] for item in ORACLE["cases"]} == set(ORACLE["scenarios"])
    Draft202012Validator.check_schema(INPUT_SCHEMA)
    Draft202012Validator.check_schema(RESULT_SCHEMA)


def test_valid_verify_and_implement_use_workflow_runner(tmp_path, monkeypatch):
    result, fakes = run_workflow(tmp_path, monkeypatch, case("valid-verify"))
    assert result["execution_status"] == "verified"
    assert (fakes.codex_calls, fakes.validation_calls, fakes.publish_calls) == (0, 0, 0)

    result, fakes = run_workflow(tmp_path, monkeypatch, case("valid-fake-implement"))
    assert result["execution_status"] == "succeeded"
    assert (fakes.codex_calls, fakes.validation_calls, fakes.publish_calls) == (1, 1, 1)


@pytest.mark.parametrize(
    "name",
    [
        "wrong-target",
        "unsupported-version",
        "malformed-input",
        "unauthorized-caller",
        "unsupported-task-type",
        "invalid-concurrency-group",
    ],
)
def test_pinned_admission_rejections(tmp_path, monkeypatch, name):
    fixture = case(name)
    status, admitted = admit(tmp_path, monkeypatch, fixture)
    assert status == fixture["expected_admission_status"]
    assert not admitted.exists()


def test_idempotency_ownership_and_create_race(tmp_path, monkeypatch):
    fixture = case("matching-managed-draft")
    fakes = WorkflowFakes(monkeypatch, [owned_pr(fixture)])
    result, _ = run_workflow(tmp_path, monkeypatch, fixture, fakes)
    assert result["execution_status"] == "duplicate-reused"
    assert fakes.codex_calls == 0

    fixture = case("ambiguous-ownership")
    fakes = WorkflowFakes(monkeypatch, [owned_pr(fixture), owned_pr(fixture, number=2)])
    result, _ = run_workflow(tmp_path, monkeypatch, fixture, fakes)
    assert (result["execution_status"], result["failure_category"]) == (
        "failed",
        "ownership",
    )

    fixture = case("create-race")
    fakes = WorkflowFakes(monkeypatch)
    fakes.race_pr = owned_pr(fixture)
    result, _ = run_workflow(tmp_path, monkeypatch, fixture, fakes)
    assert result["pull_request_url"] == fakes.race_pr.url


@pytest.mark.parametrize(
    "name",
    ["fake-codex-failure", "validation-failure", "test-failure", "publication-failure"],
)
def test_failure_projection_is_canonical_and_secret_safe(tmp_path, monkeypatch, name):
    fixture = case(name)
    fakes = WorkflowFakes(monkeypatch)
    fakes.failure = fixture["failure"]
    result, _ = run_workflow(tmp_path, monkeypatch, fixture, fakes)
    assert result["execution_status"] == "failed"
    assert result["failure_category"] == fixture["expected_failure_category"]
    assert "sk-never-print-this" not in json.dumps(result)


def test_pinned_result_and_receiver_vocabulary(tmp_path, monkeypatch):
    result, _ = run_workflow(tmp_path, monkeypatch, case("canonical-result"))
    assert result["contract_version"] == "ai-sdlc-contract/v2"
    stored: dict[str, tuple[str, dict[str, Any]]] = {}

    def deliver(value):
        digest = result_digest(value)
        old = stored.get(value["delivery_id"])
        if old and old[0] != digest:
            return "conflict"
        if old:
            return "duplicate"
        stored[value["delivery_id"]] = (digest, deepcopy(value))
        return "accepted"

    assert deliver(result) == "accepted"
    assert deliver(deepcopy(result)) == "duplicate"
    conflict = deepcopy(result)
    conflict["diagnostic_summary"] = "changed"
    assert deliver(conflict) == "conflict"


def test_workflow_pin_receiver_and_no_mutable_activation():
    text = Path(".github/workflows/codex-execute.yml").read_text()
    assert text.count(PIN) == 2
    assert "workflow_dispatch" not in text
    assert "enabled" not in text.lower()
    assert "cancel-in-progress: false" in text
    assert text.count("persist-credentials: false") == 3
    assert [p.name for p in Path(".github/workflows").glob("*codex-execute*.yml")] == [
        "codex-execute.yml"
    ]
