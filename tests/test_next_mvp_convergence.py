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
    inputs = trigger["workflow_call"]["inputs"]
    assert set(inputs) == {"execution_input_json", "concurrency_group"}
    assert all(v["required"] and v["type"] == "string" for v in inputs.values())


def test_single_pinned_adapter_and_no_activation_gate():
    text = TARGET.read_text()
    assert "c6090e5bbadcc2102a1cb91875466e9decdada1e" in text
    assert "enabled" not in text
    assert "workflow_dispatch" not in text
    assert text.count("codex-result-receiver.yml@") == 2
    assert "persist-credentials: false" in text


def test_verify_has_no_effect_credentials():
    verify = workflow()["jobs"]["verify"]
    rendered = str(verify)
    assert (
        "CODEX_API_KEY" not in rendered and "SLUGGER_PUBLICATION_TOKEN" not in rendered
    )


def test_no_legacy_contract_or_entrypoint():
    text = TARGET.read_text()
    assert (
        "execution_input_artifact" not in text and "execution_input_run_id" not in text
    )
    project = (ROOT / "pyproject.toml").read_text()
    assert "[project.scripts]" not in project
