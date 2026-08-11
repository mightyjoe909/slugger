"""Static guards for the single disabled next-MVP interface."""

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
TARGET = WORKFLOWS / "codex-execute.yml"


def _workflow() -> dict:
    loaded = yaml.safe_load(TARGET.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    # YAML 1.1 parsers interpret the unquoted key ``on`` as True.
    return loaded


def test_only_ci_and_disabled_target_workflows_remain() -> None:
    assert {path.name for path in WORKFLOWS.glob("*.yml")} == {
        "ci.yml",
        "codex-execute.yml",
    }


def test_target_has_exact_required_reusable_inputs() -> None:
    workflow = _workflow()
    trigger = workflow.get("on", workflow.get(True))
    assert set(trigger) == {"workflow_call"}
    inputs = trigger["workflow_call"]["inputs"]
    assert set(inputs) == {"execution_input_json", "concurrency_group"}
    assert all(value["required"] is True for value in inputs.values())
    assert all(value["type"] == "string" for value in inputs.values())


def test_target_is_read_only_and_fails_before_external_effects() -> None:
    text = TARGET.read_text(encoding="utf-8")
    assert _workflow()["permissions"] == {"contents": "read"}
    assert "exit 1" in text
    for prohibited in (
        "openai/codex-action",
        "gh pr create",
        "git push",
        "actions/checkout",
        "repository: Young-Consultations/",
        "ai-sdlc-v2.1.0",
        "execution_input_artifact",
        "execution_input_run_id",
    ):
        assert prohibited not in text


def test_no_installed_legacy_console_entrypoint() -> None:
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "[project.scripts]" not in project
    assert 'slugger = "cli.main:main"' not in project
