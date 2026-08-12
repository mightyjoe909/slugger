from copy import deepcopy
import pytest
from mvp.target_adapter.contract import (
    ContractError,
    validate_request,
    COMPATIBILITY_SHA,
)

SCHEMA = {
    "type": "object",
    "required": [
        "contract_version",
        "delivery_id",
        "correlation_id",
        "mode",
        "draft_pr_only",
        "target",
        "source",
        "task",
    ],
    "properties": {
        "contract_version": {"type": "string"},
        "delivery_id": {"type": "string", "minLength": 1},
        "correlation_id": {"type": "string", "minLength": 1},
        "mode": {"type": "string"},
        "draft_pr_only": {"type": "boolean"},
        "target": {"type": "object"},
        "source": {"type": "object"},
        "task": {"type": "object"},
    },
}


def payload():
    return {
        "contract_version": "ai-sdlc-contract/v2",
        "delivery_id": "delivery-1",
        "correlation_id": "corr-1",
        "mode": "implement",
        "draft_pr_only": True,
        "target": {"repository": "Young-Consultations/slugger", "executor": "codex"},
        "source": {
            "repository": "Young-Consultations/portfolio-tasks",
            "issue_number": 114,
        },
        "task": {
            "id": "task-114",
            "type": "feature",
            "instructions": "Implement safe work",
        },
    }


def valid(value=None, **kw):
    return validate_request(
        value or payload(),
        schema=SCHEMA,
        concurrency_group=kw.get("group", "slugger:delivery-1"),
        caller_repository=kw.get("caller", "Young-Consultations/.github"),
    )


def test_pin_and_valid_request():
    assert COMPATIBILITY_SHA == "c6090e5bbadcc2102a1cb91875466e9decdada1e"
    assert valid().delivery_id == "delivery-1"


def test_no_activation_field_is_required_or_enforced():
    assert valid().mode == "implement"


def test_unauthorized_caller():
    with pytest.raises(ContractError, match="caller"):
        valid(caller="Young-Consultations/portfolio-tasks")


def test_wrong_target():
    p = payload()
    p["target"]["repository"] = "Young-Consultations/other"
    with pytest.raises(ContractError, match="wrong target"):
        valid(p)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("contract_version", "v1", "version"),
        ("mode", "deploy", "mode"),
        ("draft_pr_only", False, "draft"),
    ],
)
def test_unsupported(field, value, message):
    p = payload()
    p[field] = value
    with pytest.raises(ContractError, match=message):
        valid(p)


def test_unsupported_task_type():
    p = payload()
    p["task"]["type"] = "release"
    with pytest.raises(ContractError, match="task type"):
        valid(p)


def test_malformed_input():
    p = payload()
    del p["delivery_id"]
    with pytest.raises(ContractError, match="schema"):
        valid(p)


def test_invalid_concurrency():
    with pytest.raises(ContractError, match="concurrency"):
        valid(group="bad group")


def test_changed_payload_changes_digest():
    a = valid()
    p = deepcopy(payload())
    p["task"]["instructions"] = "changed"
    assert valid(p).payload_digest != a.payload_digest
