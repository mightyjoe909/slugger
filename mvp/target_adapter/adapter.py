"""Effect-injected target coordinator used by production and conformance tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any, Protocol

from .contract import ExecutionRequest
from .ownership import ManagedPullRequest, OwnershipState, branch_name, reconcile
from .result import build_result


class Repository(Protocol):
    def pull_requests(self) -> list[ManagedPullRequest]: ...
    def branch_exists(self, branch: str) -> bool: ...
    def publish(self, request: ExecutionRequest, branch: str) -> ManagedPullRequest: ...


@dataclass
class TargetAdapter:
    repository: Repository
    codex: Callable[[ExecutionRequest], None]
    validate_candidate: Callable[[ExecutionRequest], None]

    def execute(self, request: ExecutionRequest) -> dict[str, Any]:
        decision = reconcile(
            request,
            self.repository.pull_requests(),
            branch_exists=self.repository.branch_exists(
                branch_name(request.delivery_id)
            ),
        )
        if decision.state is OwnershipState.AMBIGUOUS:
            return build_result(
                request, "failed", summary=decision.reason, failure_category="ownership"
            )
        if decision.state is OwnershipState.REUSE:
            assert decision.pull_request is not None
            return build_result(
                request,
                "duplicate-reused",
                summary="managed draft reused",
                branch=decision.branch,
                pull_request_url=decision.pull_request.url,
            )
        if request.mode == "verify":
            return build_result(request, "verified", summary="request verified")
        try:
            self.codex(request)
            self.validate_candidate(request)
            pr = self.repository.publish(request, decision.branch)
        except TimeoutError as exc:
            return build_result(
                request, "failed", summary=str(exc), failure_category="timeout"
            )
        except Exception as exc:
            return build_result(
                request, "failed", summary=str(exc), failure_category="execution"
            )
        return build_result(
            request,
            "succeeded",
            summary="validated draft created",
            branch=decision.branch,
            pull_request_url=pr.url,
        )
