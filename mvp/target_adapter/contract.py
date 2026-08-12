"""Pinned wire-contract validation and target-local policy."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Mapping

import importlib.util

COMPATIBILITY_SHA = "c6090e5bbadcc2102a1cb91875466e9decdada1e"
CONTRACT_VERSION = "ai-sdlc-contract/v2"
TARGET_REPOSITORY = "Young-Consultations/slugger"
ROUTER_REPOSITORY = "Young-Consultations/.github"
ALLOWED_TASK_TYPES = frozenset(
    {"automation", "bug-fix", "documentation", "feature", "testing"}
)
ALLOWED_MODES = frozenset({"verify", "implement"})
_CONCURRENCY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}$")


class ContractError(ValueError):
    """A request is not safe to admit."""


@dataclass(frozen=True)
class ExecutionRequest:
    payload: Mapping[str, Any]
    delivery_id: str
    correlation_id: str
    task_id: str
    task_type: str
    instructions: str
    mode: str
    source_repository: str
    source_issue: int
    payload_digest: str


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{field} must be a non-empty string")
    return value.strip()


def canonical_digest(payload: Mapping[str, Any]) -> str:
    """Bind the entire immutable canonical request, excluding transport metadata."""
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(encoded.encode()).hexdigest()


def _fallback_schema_check(
    value: Any, schema: Mapping[str, Any], path: str = "$"
) -> None:
    """Small offline test fallback; production installs the official validator."""
    expected = schema.get("type")
    types = {
        "object": dict,
        "array": list,
        "string": str,
        "integer": int,
        "boolean": bool,
        "null": type(None),
    }
    if expected in types and (
        not isinstance(value, types[expected])
        or expected == "integer"
        and isinstance(value, bool)
    ):
        raise ContractError(
            f"execution-input/v2 schema error at {path}: expected {expected}"
        )
    if isinstance(value, dict):
        for name in schema.get("required", []):
            if name not in value:
                raise ContractError(
                    f"execution-input/v2 schema error at {path}: missing {name}"
                )
        for name, child in schema.get("properties", {}).items():
            if name in value and isinstance(child, Mapping):
                _fallback_schema_check(value[name], child, f"{path}.{name}")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            raise ContractError(
                f"execution-input/v2 schema error at {path}: string too short"
            )
        if schema.get("format") == "uri" and "://" not in value:
            raise ContractError(
                f"execution-input/v2 schema error at {path}: invalid uri format"
            )


def validate_schema(payload: Mapping[str, Any], schema: Mapping[str, Any]) -> None:
    """Validate using jsonschema with formats; retain a hermetic test fallback."""
    if importlib.util.find_spec("jsonschema") is None:
        _fallback_schema_check(payload, schema)
        return
    from jsonschema import FormatChecker
    from jsonschema.validators import validator_for

    cls = validator_for(schema)
    cls.check_schema(schema)
    errors = sorted(
        cls(schema, format_checker=FormatChecker()).iter_errors(payload),
        key=lambda e: list(e.path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        raise ContractError(
            f"execution-input/v2 schema error at {location}: {error.message}"
        )


def validate_request(
    payload: Mapping[str, Any],
    *,
    schema: Mapping[str, Any],
    concurrency_group: str,
    caller_repository: str,
) -> ExecutionRequest:
    """Apply canonical validation plus Slugger defense-in-depth policy.

    Activation is intentionally absent: the organization router owns mutable
    activation and dispatches only after enforcing it.
    """
    if caller_repository != ROUTER_REPOSITORY:
        raise ContractError("caller is not the organization router")
    if not _CONCURRENCY.fullmatch(concurrency_group):
        raise ContractError("concurrency_group is invalid")
    validate_schema(payload, schema)
    if payload.get("contract_version") != CONTRACT_VERSION:
        raise ContractError("unsupported contract version")
    target = payload.get("target")
    task = payload.get("task")
    source = payload.get("source")
    if not all(isinstance(item, Mapping) for item in (target, task, source)):
        raise ContractError("target, task, and source objects are required")
    assert (
        isinstance(target, Mapping)
        and isinstance(task, Mapping)
        and isinstance(source, Mapping)
    )
    if target.get("repository") != TARGET_REPOSITORY:
        raise ContractError("wrong target repository")
    if str(target.get("executor", "")).lower() != "codex":
        raise ContractError("unsupported executor")
    task_type = _text(task.get("type"), "task.type")
    if task_type not in ALLOWED_TASK_TYPES:
        raise ContractError("unsupported task type")
    mode = _text(payload.get("mode"), "mode")
    if mode not in ALLOWED_MODES:
        raise ContractError("unsupported execution mode")
    if payload.get("draft_pr_only") is not True:
        raise ContractError("draft_pr_only must be true")
    issue = source.get("issue_number")
    if not isinstance(issue, int) or issue < 1:
        raise ContractError("source.issue_number must be positive")
    return ExecutionRequest(
        payload=payload,
        delivery_id=_text(payload.get("delivery_id"), "delivery_id"),
        correlation_id=_text(payload.get("correlation_id"), "correlation_id"),
        task_id=_text(task.get("id"), "task.id"),
        task_type=task_type,
        instructions=_text(task.get("instructions"), "task.instructions"),
        mode=mode,
        source_repository=_text(source.get("repository"), "source.repository"),
        source_issue=issue,
        payload_digest=canonical_digest(payload),
    )
