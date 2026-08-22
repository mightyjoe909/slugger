"""Static guards for the single canonical next-MVP interface."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github/workflows"
TARGET = WORKFLOWS / "codex-execute.yml"


def workflow():
    value = yaml.safe_load(TARGET.read_text())
    assert isinstance(value, dict)
    return value


def test_only_ci_and_target_workflows_remain():
    assert {p.name for p in WORKFLOWS.glob("*.yml")} == {"ci.yml", "codex-execute.yml"}


def test_exact_inputs():
    trigger = workflow().get("on", workflow().get(True))
    inputs = trigger["workflow_dispatch"]["inputs"]
    assert set(inputs) == {"execution_input_json", "concurrency_group"}
    assert all(v["required"] and v["type"] == "string" for v in inputs.values())


def test_single_pinned_adapter_and_no_activation_gate():
    text = TARGET.read_text()
    assert "codex-result-receiver.yml@ai-sdlc-v2.3.1" in text
    assert "enabled" not in text
    assert "workflow_dispatch" in text
    assert "workflow_call" not in text
    assert text.count("codex-result-receiver.yml@") == 1
    assert "persist-credentials: false" in text


def test_result_delivery_has_only_its_narrow_token():
    jobs = workflow()["jobs"]
    assert "CODEX_RESULT_TOKEN" not in str(jobs["execute"])
    report = str(jobs["report"])
    assert "CODEX_RESULT_TOKEN" in report
    assert "OPENAI_API_KEY" not in report
    assert "TARGET_PUBLICATION_TOKEN" not in report


def test_no_legacy_contract_or_entrypoint():
    text = TARGET.read_text()
    assert (
        "execution_input_artifact" not in text and "execution_input_run_id" not in text
    )
    project = (ROOT / "pyproject.toml").read_text()
    assert "[project.scripts]" not in project
    assert not (ROOT / "mvp/target_adapter").exists()
    assert not (ROOT / "tests/conformance").exists()
    assert (ROOT / "tests/fixtures/mvp-v2/manifest.json").is_file()
