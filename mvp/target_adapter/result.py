"""Canonical result construction, validation, and safe diagnostics."""

from __future__ import annotations

import json
import re
from typing import Any, Mapping

from .contract import CONTRACT_VERSION, ExecutionRequest, validate_schema

_SECRET = re.compile(r"(?i)(gh[pousr]_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]+|bearer\s+\S+)")


def safe_message(value: object, limit: int = 512) -> str:
    text = _SECRET.sub("[REDACTED]", str(value)).replace("\x00", "")
    return text[:limit]


def build_result(
    request: ExecutionRequest,
    status: str,
    *,
    summary: str,
    failure_category: str | None = None,
    branch: str | None = None,
    pull_request_url: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "delivery_id": request.delivery_id,
        "correlation_id": request.correlation_id,
        "target": {"repository": "Young-Consultations/slugger"},
        "execution_status": status,
        "diagnostic_summary": safe_message(summary),
        "branch": branch,
        "pull_request_url": pull_request_url,
    }
    if failure_category is not None:
        result["failure_category"] = failure_category
    return result


def validate_result(result: Mapping[str, Any], schema: Mapping[str, Any]) -> None:
    validate_schema(result, schema)


def result_digest(result: Mapping[str, Any]) -> str:
    import hashlib

    return hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
