"""Offline execution of the pinned TC-MVP-CI-001 target oracle.

The manifest is a provenance/selection file, not a replacement wire schema. Wire
validation remains the responsibility of the canonical schemas consumed by the
adapter admission path.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, replace
import json
from pathlib import Path
from typing import Any

import pytest

from mvp.target_adapter.adapter import TargetAdapter
from mvp.target_adapter.contract import ContractError, validate_request
from mvp.target_adapter.ownership import ManagedPullRequest, branch_name, marker
from mvp.target_adapter.result import result_digest
from tests.test_target_adapter_contract import SCHEMA, payload

PIN = "c6090e5bbadcc2102a1cb91875466e9decdada1e"
ORACLE = json.loads(Path("tests/conformance/fixtures/TC-MVP-CI-001.json").read_text())


@dataclass
class Effects:
    codex_requests: int = 0
    branches: int = 0
    commits: int = 0
    pushes: int = 0
    pull_requests: int = 0
    merge_release_deploy_production: int = 0
    secret_output: list[str] = field(default_factory=list)

    def assert_normal_ci_is_effect_free(self) -> None:
        assert self == Effects()


class FakeRepository:
    def __init__(self, effects: Effects, prs: list[ManagedPullRequest] | None = None):
        self.effects = effects
        self.prs = list(prs or [])
        self.unowned_branch = False
        self.publish_error: Exception | None = None
        self.race_pr: ManagedPullRequest | None = None

    def pull_requests(self) -> list[ManagedPullRequest]:
        return self.prs

    def branch_exists(self, unused_branch: str) -> bool:
        return self.unowned_branch

    def publish(self, request, branch: str) -> ManagedPullRequest:
        # This is deliberately an in-memory publication seam. Recording a real
        # mutation here would make the effect trap fail.
        if self.publish_error:
            raise self.publish_error
        if self.race_pr:
            self.prs.append(self.race_pr)
            return self.race_pr
        pr = ManagedPullRequest(
            1,
            "https://example.invalid/pr/1",
            "open",
            True,
            branch,
            "main",
            marker(request),
        )
        self.prs.append(pr)
        return pr


class FakeReceiver:
    def __init__(self) -> None:
        self.results: dict[str, tuple[str, dict[str, Any]]] = {}
        self.fail = False

    def deliver(self, result: dict[str, Any]) -> str:
        if self.fail:
            raise RuntimeError("receiver unavailable")
        key = result["delivery_id"]
        digest = result_digest(result)
        old = self.results.get(key)
        if old and old[0] != digest:
            return "conflict"
        if old:
            return "duplicate"
        self.results[key] = (digest, deepcopy(result))
        return "accepted"


def request(mode: str = "implement", value: dict[str, Any] | None = None):
    value = deepcopy(value or payload())
    value["mode"] = mode
    return validate_request(
        value,
        schema=SCHEMA,
        concurrency_group="slugger:delivery-1",
        caller_repository="Young-Consultations/.github",
    )


def owned_pr(req, **changes) -> ManagedPullRequest:
    pr = ManagedPullRequest(
        1,
        "https://example.invalid/pr/1",
        "open",
        True,
        branch_name(req.delivery_id),
        "main",
        marker(req),
    )
    return replace(pr, **changes)


def test_oracle_identity_and_complete_target_scenario_selection():
    assert ORACLE["organization_revision"] == PIN
    assert ORACLE["fixture_set"] == "TC-MVP-CI-001"
    assert ORACLE["target_repository"] == "Young-Consultations/slugger"
    assert len(ORACLE["scenarios"]) == 22


def test_admission_and_verify_cases():
    effects = Effects()
    result = TargetAdapter(FakeRepository(effects), pytest.fail, pytest.fail).execute(
        request("verify")
    )
    assert result["execution_status"] == "verified"
    effects.assert_normal_ci_is_effect_free()

    cases = []
    wrong = payload()
    wrong["target"]["repository"] = "Young-Consultations/other"
    cases.append(wrong)
    version = payload()
    version["contract_version"] = "ai-sdlc-contract/v1"
    cases.append(version)
    malformed = payload()
    del malformed["delivery_id"]
    cases.append(malformed)
    task_type = payload()
    task_type["task"]["type"] = "release"
    cases.append(task_type)
    for value in cases:
        with pytest.raises(ContractError):
            request(value=value)
    with pytest.raises(ContractError, match="caller"):
        validate_request(
            payload(),
            schema=SCHEMA,
            concurrency_group="group",
            caller_repository="attacker/repo",
        )
    with pytest.raises(ContractError, match="concurrency"):
        validate_request(
            payload(),
            schema=SCHEMA,
            concurrency_group="bad group",
            caller_repository="Young-Consultations/.github",
        )


def test_fake_implement_idempotency_ownership_and_create_race():
    effects = Effects()
    repo = FakeRepository(effects)
    fake_calls: list[str] = []
    adapter = TargetAdapter(
        repo,
        lambda unused: fake_calls.append("fake-codex"),
        lambda unused: fake_calls.append("validation"),
    )
    first = adapter.execute(request())
    assert first["execution_status"] == "succeeded"
    assert adapter.execute(request())["execution_status"] == "duplicate-reused"
    assert fake_calls == ["fake-codex", "validation"]

    req = request()
    assert (
        TargetAdapter(
            FakeRepository(effects, [owned_pr(req)]), pytest.fail, pytest.fail
        ).execute(req)["execution_status"]
        == "duplicate-reused"
    )
    ambiguous = [owned_pr(req), owned_pr(req, number=2)]
    assert (
        TargetAdapter(
            FakeRepository(effects, ambiguous), pytest.fail, pytest.fail
        ).execute(req)["failure_category"]
        == "ownership"
    )
    changed = payload()
    changed["task"]["instructions"] = "different immutable work"
    assert (
        TargetAdapter(
            FakeRepository(effects, [owned_pr(req)]), pytest.fail, pytest.fail
        ).execute(request(value=changed))["failure_category"]
        == "ownership"
    )

    race_repo = FakeRepository(effects)
    race_repo.race_pr = owned_pr(req)
    assert (
        TargetAdapter(race_repo, lambda unused: None, lambda unused: None).execute(req)[
            "pull_request_url"
        ]
        == race_repo.race_pr.url
    )
    effects.assert_normal_ci_is_effect_free()


@pytest.mark.parametrize("failure", ["codex", "validation", "test", "publication"])
def test_failure_projection_is_canonical_and_secret_safe(failure: str):
    effects = Effects()
    repo = FakeRepository(effects)
    secret = "sk-super-secret-value"

    def codex(unused):
        return None

    def validation(unused):
        return None

    if failure == "codex":

        def codex(unused):
            raise RuntimeError(secret)

    elif failure in {"validation", "test"}:

        def validation(unused):
            raise RuntimeError(f"{failure} failed {secret}")

    else:
        repo.publish_error = RuntimeError(f"publication failed {secret}")
    result = TargetAdapter(repo, codex, validation).execute(request())
    assert result["execution_status"] == "failed"
    assert result["failure_category"] == "execution"
    assert secret not in json.dumps(result)
    effects.assert_normal_ci_is_effect_free()


def test_result_receiver_and_redelivery_semantics():
    effects = Effects()
    result = TargetAdapter(FakeRepository(effects), pytest.fail, pytest.fail).execute(
        request("verify")
    )
    assert result["contract_version"] == "ai-sdlc-contract/v2"
    assert result["target"] == {"repository": "Young-Consultations/slugger"}
    receiver = FakeReceiver()
    assert receiver.deliver(result) == "accepted"
    assert receiver.deliver(deepcopy(result)) == "duplicate"
    conflict = deepcopy(result)
    conflict["diagnostic_summary"] = "changed"
    assert receiver.deliver(conflict) == "conflict"
    receiver.fail = True
    with pytest.raises(RuntimeError, match="unavailable"):
        receiver.deliver(result)
    effects.assert_normal_ci_is_effect_free()


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
