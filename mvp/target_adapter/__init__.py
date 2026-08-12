"""Canonical organization target adapter for Slugger."""

from .adapter import TargetAdapter
from .contract import (
    COMPATIBILITY_SHA,
    ContractError,
    ExecutionRequest,
    validate_request,
)
from .ownership import ManagedPullRequest, OwnershipDecision, OwnershipState

__all__ = [
    "COMPATIBILITY_SHA",
    "ContractError",
    "ExecutionRequest",
    "ManagedPullRequest",
    "OwnershipDecision",
    "OwnershipState",
    "TargetAdapter",
    "validate_request",
]
