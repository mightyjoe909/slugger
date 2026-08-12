"""Hermetic conformance harness invariants; the pinned oracle is fetched in CI."""

from pathlib import Path


def test_conformance_workflow_is_immutable_and_effect_free_by_default():
    text = Path(".github/workflows/codex-execute.yml").read_text()
    assert "c6090e5bbadcc2102a1cb91875466e9decdada1e" in text
    assert "workflow_dispatch" not in text
    assert "cancel-in-progress: false" in text
    assert "CODEX_RESULT_TOKEN" in text


def test_no_parallel_target_workflow():
    workflows = Path(".github/workflows")
    assert [p.name for p in workflows.glob("*codex-execute*.yml")] == [
        "codex-execute.yml"
    ]
