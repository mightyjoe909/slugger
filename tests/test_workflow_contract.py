"""Workflow, credential-boundary, and single-path security regressions."""

import re
from pathlib import Path

WORKFLOWS = Path(".github/workflows")
TARGET = WORKFLOWS / "codex-execute.yml"


def test_exactly_one_active_target_path_and_two_expected_workflows() -> None:
    assert tuple(sorted(WORKFLOWS.glob("*.yml"))) == (
        WORKFLOWS / "ci.yml",
        TARGET,
    )
    for obsolete in (
        Path("mvp/target_adapter"),
        Path("tests/conformance"),
        Path("scripts/generate_conformance_report.py"),
        Path("artifacts/conformance/TC-MVP-CI-001-v1.md"),
    ):
        assert not obsolete.exists()


def test_target_exposes_exact_two_input_dispatch_and_pinned_receiver() -> None:
    text = TARGET.read_text(encoding="utf-8")
    trigger = text.split("on:", 1)[1].split("permissions:", 1)[0]
    inputs = trigger.split("inputs:", 1)[1]
    assert "workflow_dispatch:" in trigger
    assert "workflow_call:" not in text
    assert re.findall(r"^      ([a-z_]+):$", inputs, re.MULTILINE) == [
        "execution_input_json",
        "concurrency_group",
    ]
    assert "codex-result-receiver.yml@ai-sdlc-v2.3.1" in text
    assert "CODEX_TRUSTED_JOURNAL_AUTHORS" not in text
    assert "secrets: inherit" not in text
    receiver = text.split("  report:", 1)[1]
    assert receiver.count("CODEX_RESULT_TOKEN:") == 1
    assert "OPENAI_API_KEY" not in receiver
    assert "TARGET_PUBLICATION_TOKEN" not in receiver


def test_target_has_least_privilege_and_credential_separation() -> None:
    text = TARGET.read_text(encoding="utf-8")
    assert "permissions:\n  contents: read" in text
    assert "persist-credentials: false" in text
    assert "fetch-depth: 0" in text
    assert "environment: slugger-codex-production" in text
    assert "@openai/codex@0.63.0" in text
    assert "CODEX_TARGET_TRUSTED_CALLERS" in text
    assert "TARGET_PUBLICATION_TOKEN" in text
    assert "OPENAI_API_KEY" in text
    assert "gh pr merge" not in text
    assert "git push origin main" not in text
    references = re.findall(r"(?:uses: )\S+@(\S+)", text)
    commit_references = [ref for ref in references if not ref.startswith("ai-sdlc-")]
    assert commit_references and all(
        re.fullmatch(r"[0-9a-f]{40}", ref) for ref in commit_references
    )


def test_normal_ci_has_no_codex_or_publication_effect() -> None:
    text = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8").lower()
    for forbidden in (
        "openai_api_key",
        "target_publication_token",
        "codex exec",
        "git checkout -b",
        "git push",
        "gh pr create",
        "gh pr merge",
        "gh release",
        "environment:",
        "secrets.",
    ):
        assert forbidden not in text
    assert "python scripts/run_tc_mvp_ci_001.py" in text
    assert "git diff --exit-code -- .ai-sdlc/conformance/tc-mvp-ci-001.json" in text
