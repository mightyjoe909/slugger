"""Run TC-MVP-CI-001 through the real repository adapter with effect traps."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.codex_target_adapter import (  # noqa: E402
    TARGET,
    AdapterError,
    Ownership,
    canonical_digest,
    run_adapter,
)

FIXTURES = ROOT / "tests/fixtures/mvp-v2"
PIN_PATH = ROOT / "config/mvp-conformance-pin.json"
PIN_FIELDS = {
    "pin_format_version",
    "organization_repository",
    "compatibility_sha",
    "fixture_set",
    "fixture_version",
    "adapter_revision",
    "compatibility_files",
    "target_files",
}
EXPECTED_COMPATIBILITY_SHA = "e27b8a541afbd27b4be5606a19ffa43637ad312a"
EXPECTED_COMPATIBILITY_BLOBS = {
    "contracts/task-contract.schema.json": "d95673363eb7f825eb64b73ddb0468c787078ce4",
    "contracts/execution-input.schema.json": "b2b16cfda619c82d73a5e78ae34566feb6b83224",
    "contracts/execution-result.schema.json": "02ba5fd11b6903f50eccc283679c0b5ac85c4714",
    "tests/fixtures/mvp-v2/manifest.json": "1656140614973245cf288380e6bcc89f83d8e51f",
    "tests/fixtures/mvp-v2/scenarios.json": "d0b20b7272bcb38871cb07e51f6a1141eb1f4f04",
    "tests/fixtures/mvp-v2/expected-results.json": "b45c6921f029220b2f3138d5cd2d9443499a3171",
}
COMPATIBILITY_FILES = set(EXPECTED_COMPATIBILITY_BLOBS)
TARGET_FILES = {
    ".github/workflows/codex-execute.yml",
    "scripts/codex_target_adapter.py",
    "scripts/validate_repository.py",
    "scripts/test_codex_execute_contract.py",
}
ROUTER_REJECTIONS = {
    "unauthorized-approval",
    "stale-approval",
    "withdrawn-approval",
    "queued-task-at-admission",
    "material-change-old-task-id",
    "disabled-target",
}


@dataclass
class Effects:
    """Counters whose nonzero value would invalidate no-real-effect evidence."""

    codex_calls: int = 0
    real_branches_created: int = 0
    real_commits_created: int = 0
    real_pushes: int = 0
    real_pull_requests_created: int = 0
    merge_actions: int = 0
    release_actions: int = 0
    deployment_actions: int = 0
    production_actions: int = 0
    secret_outputs: int = 0


TRAPPED_EFFECTS = tuple(Effects.__dataclass_fields__)


class TrappedTargetEffects:
    """Dependency-injected target seam; it cannot call Codex, GitHub, or git."""

    def __init__(
        self,
        traps: Effects,
        *,
        found: list[dict[str, Any]] | None = None,
        codex_failure: bool = False,
        validation: tuple[bool, str] = (True, "passed"),
        publish_failure: str | None = None,
        race: list[dict[str, Any]] | None = None,
        branch_exists: bool | None = None,
        race_branch_exists: bool | None = None,
    ) -> None:
        self.traps = traps
        self.found = found or []
        self.codex_failure = codex_failure
        self.validation = validation
        self.publish_failure = publish_failure
        self.race = race
        self.branch_exists = (
            bool(self.found) if branch_exists is None else branch_exists
        )
        self.race_branch_exists = (
            bool(race) if race_branch_exists is None else race_branch_exists
        )
        self.calls = {"discover": 0, "codex": 0, "validate": 0, "publish": 0}

    def discover(
        self, branch: str, delivery_id: str, timeout_seconds: float
    ) -> Ownership:
        self.calls["discover"] += 1
        if self.calls["discover"] > 1 and self.race is not None:
            return Ownership(self.race_branch_exists, self.race)
        return Ownership(self.branch_exists, self.found)

    def codex(self, instructions: str, timeout_seconds: float) -> None:
        # This is a deterministic fake executor. The real Codex trap remains zero.
        self.calls["codex"] += 1
        if self.codex_failure:
            raise AdapterError("codex-runtime", "Codex execution failed", "failed")

    def validate_candidate(self, timeout_seconds: float) -> tuple[bool, str]:
        self.calls["validate"] += 1
        return self.validation

    def publish(
        self, branch: str, delivery_id: str, digest: str, timeout_seconds: float
    ) -> str:
        # No branch, commit, push, or PR API is reachable from this seam.
        self.calls["publish"] += 1
        if self.publish_failure:
            raise AdapterError("publication", self.publish_failure, "failed")
        return "https://github.com/Young-Consultations/slugger/pull/7"


class TrappedReceiver:
    """In-memory receiver/source projection used only after a real adapter result."""

    def __init__(self) -> None:
        self.received: dict[str, str] = {}
        self.forward_count = 0

    def receive(self, result: dict[str, Any], *, binding_valid: bool = True) -> str:
        if not binding_valid:
            return "rejected"
        delivery_id = str(result["delivery_id"])
        canonical = json.dumps(result, sort_keys=True, separators=(",", ":"))
        prior = self.received.get(delivery_id)
        if prior is not None:
            return "accepted" if prior == canonical else "ambiguous-rejected"
        self.received[delivery_id] = canonical
        self.forward_count += 1
        return "accepted"


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def pin_revision(pin: dict[str, Any]) -> str:
    material = dict(pin)
    material["adapter_revision"] = None
    canonical = json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def validate_pin(pin: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if set(pin) != PIN_FIELDS or pin.get("pin_format_version") != 2:
        return ["conformance pin has an invalid shape"]
    if pin.get("organization_repository") != "Young-Consultations/.github":
        errors.append("compatibility pin has the wrong organization repository")
    if pin.get("compatibility_sha") != EXPECTED_COMPATIBILITY_SHA:
        errors.append("compatibility pin has the wrong immutable revision")
    if (
        pin.get("fixture_set") != "TC-MVP-CI-001"
        or pin.get("fixture_version") != "2.3.0"
    ):
        errors.append("compatibility pin has the wrong fixture identity")
    compatibility_files = pin.get("compatibility_files")
    target_files = pin.get("target_files")
    if (
        not isinstance(compatibility_files, dict)
        or set(compatibility_files) != COMPATIBILITY_FILES
    ):
        errors.append("compatibility pin has the wrong shared file set")
        compatibility_files = {}
    if not isinstance(target_files, dict) or set(target_files) != TARGET_FILES:
        errors.append("compatibility pin has the wrong target file set")
        target_files = {}
    expected_revision = pin_revision(pin)
    if pin.get("adapter_revision") != expected_revision:
        errors.append("adapter revision does not match the canonical conformance pin")
    if compatibility_files != EXPECTED_COMPATIBILITY_BLOBS:
        errors.append(
            "pinned compatibility identities differ from the approved immutable revision"
        )
    for relative, expected in compatibility_files.items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"pinned file is missing: {relative}")
        elif git_blob_sha1(path.read_bytes()) != expected:
            errors.append(f"pinned file is incompatible: {relative}")
    for relative, expected in target_files.items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"pinned target file is missing: {relative}")
        elif git_blob_sha1(path.read_bytes()) != expected:
            errors.append(f"pinned target file is incompatible: {relative}")
    return errors


def _payload() -> dict[str, Any]:
    delivery_id = "delivery-42"
    return {
        "contract_version": "ai-sdlc-contract/v2",
        "correlation_id": "correlation-42",
        "delivery_id": delivery_id,
        "source_issue": "Young-Consultations/portfolio-tasks#135",
        "target_repository": TARGET,
        "task_type": "documentation",
        "execution_mode": "implement",
        "project": "slugger",
        "priority": "p0",
        "executor": "codex",
        "parallel_safe": False,
        "draft_pr_only": True,
        "instructions": "Update the approved Slugger artifact without external effects.",
        "requested_branch": f"codex/{delivery_id}",
        "concurrency_group": "ai-sdlc.slugger.delivery-42",
        "timeout_minutes": 40,
    }


def _managed(payload: dict[str, Any], *, digest: str | None = None) -> dict[str, Any]:
    return {
        "url": "https://github.com/Young-Consultations/slugger/pull/7",
        "state": "OPEN",
        "draft": True,
        "digest": digest or canonical_digest(payload),
    }


def _adapter(
    payload: dict[str, Any],
    effects: TrappedTargetEffects,
    *,
    raw: str | None = None,
    caller: str = "router-app",
) -> dict[str, Any]:
    serialized = json.dumps(payload) if raw is None else raw
    return run_adapter(
        serialized,
        payload["concurrency_group"],
        caller,
        {"router-app"},
        effects,
