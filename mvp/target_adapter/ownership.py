"""Deterministic, fail-closed managed draft ownership."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
from typing import Iterable

from .contract import ExecutionRequest, TARGET_REPOSITORY

MARKER_NAME = "ai-sdlc-delivery-id"
_MARKER = re.compile(r"<!-- ai-sdlc-delivery-id: (\{.*?\}) -->", re.DOTALL)


@dataclass(frozen=True)
class ManagedPullRequest:
    number: int
    url: str
    state: str
    draft: bool
    head: str
    base: str
    body: str


class OwnershipState(str, Enum):
    NEW = "new"
    REUSE = "duplicate-reused"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class OwnershipDecision:
    state: OwnershipState
    branch: str
    pull_request: ManagedPullRequest | None = None
    reason: str = ""


def branch_name(delivery_id: str) -> str:
    digest = hashlib.sha256(delivery_id.encode()).hexdigest()[:20]
    return f"slugger/codex-delivery-{digest}"


def marker(request: ExecutionRequest) -> str:
    value = {
        "delivery_id": request.delivery_id,
        "payload_digest": request.payload_digest,
        "target_repository": TARGET_REPOSITORY,
    }
    return f"<!-- {MARKER_NAME}: {json.dumps(value, sort_keys=True, separators=(',', ':'))} -->"


def parse_marker(body: str) -> dict[str, str] | None:
    matches = _MARKER.findall(body)
    if len(matches) != 1:
        return None
    try:
        value = json.loads(matches[0])
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def reconcile(
    request: ExecutionRequest, prs: Iterable[ManagedPullRequest], *, branch_exists: bool
) -> OwnershipDecision:
    branch = branch_name(request.delivery_id)
    candidates = [
        pr
        for pr in prs
        if pr.head == branch
        or (parse_marker(pr.body) or {}).get("delivery_id") == request.delivery_id
    ]
    if len(candidates) != 1:
        if candidates or branch_exists:
            return OwnershipDecision(
                OwnershipState.AMBIGUOUS, branch, reason="ownership is not unique"
            )
        return OwnershipDecision(OwnershipState.NEW, branch)
    pr = candidates[0]
    expected = parse_marker(marker(request))
    if (
        parse_marker(pr.body) != expected
        or pr.state.lower() != "open"
        or not pr.draft
        or pr.head != branch
        or pr.base != "main"
    ):
        return OwnershipDecision(
            OwnershipState.AMBIGUOUS,
            branch,
            pr,
            "owned draft shape or digest conflicts",
        )
    return OwnershipDecision(OwnershipState.REUSE, branch, pr)
