from dataclasses import replace
from mvp.target_adapter.contract import validate_request
from mvp.target_adapter.ownership import (
    ManagedPullRequest,
    OwnershipState,
    branch_name,
    marker,
    reconcile,
)
from tests.test_target_adapter_contract import SCHEMA, payload


def req():
    return validate_request(
        payload(),
        schema=SCHEMA,
        concurrency_group="group",
        caller_repository="Young-Consultations/.github",
    )


def pr(r, **changes):
    value = ManagedPullRequest(
        1,
        "https://example/pr/1",
        "open",
        True,
        branch_name(r.delivery_id),
        "main",
        marker(r),
    )
    return replace(value, **changes)


def test_matching_draft_reused():
    assert (
        reconcile(req(), [pr(req())], branch_exists=True).state is OwnershipState.REUSE
    )


def test_ambiguous_multiple_drafts():
    assert (
        reconcile(
            req(), [pr(req()), replace(pr(req()), number=2)], branch_exists=True
        ).state
        is OwnershipState.AMBIGUOUS
    )


def test_unowned_branch_fails_closed():
    assert reconcile(req(), [], branch_exists=True).state is OwnershipState.AMBIGUOUS


def test_changed_payload_same_delivery_conflicts():
    a = req()
    value = payload()
    value["task"]["instructions"] = "changed"
    b = validate_request(
        value,
        schema=SCHEMA,
        concurrency_group="group",
        caller_repository="Young-Consultations/.github",
    )
    assert reconcile(b, [pr(a)], branch_exists=True).state is OwnershipState.AMBIGUOUS
