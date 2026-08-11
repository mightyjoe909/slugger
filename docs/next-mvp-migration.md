# Next-MVP convergence inventory

**Status:** current migration record. This record applies the authority order in
[`AI_CONTEXT.md`](../AI_CONTEXT.md) and does not create requirements or contracts.
The controlling baseline is [`next-mvp.md`](next-mvp.md).

## Disposition rules

* **KEEP** means the artifact is authoritative, required governance, or neutral
  project infrastructure.
* **MODIFY** means retain the artifact but remove a conflicting current-path claim
  or trigger.
* **REMOVE** means no authoritative requirement needs the live path and retaining
  it creates a duplicate execution, publication, or repository-owned interface.
* **DEFER** means retain visibly quarantined blueprint material because ADR-010
  leaves its extraction/removal decision open; it is not supported or executable
  through a packaged command or workflow.

## Migration table

| Candidate path/responsibility | Decision | Result and authoritative reason |
|---|---|---|
| `AI_CONTEXT.md`, `docs/VISION.md`, `docs/next-mvp.md`, `docs/requirements/**`, `docs/architecture/**`, current interface documents | KEEP | These are the ordered authoritative policy, baseline, requirements, design, ADR, and interface sources. |
| `.github/workflows/codex-execute.yml` | MODIFY | It is the sole eventual entry point (FR-INT-01/02), now limited to required strings `execution_input_json` and `concurrency_group`. Because the registry and receiver are blocked, it fails before checkout or mutation and cannot invoke Codex or publish. |
| Obsolete `execution_input_artifact`, `execution_input_run_id`, v2.1 tag/package checkout, target-side label approval, locally constructed result, and direct publication in `codex-execute.yml` | REMOVE | The 2.2.0 baseline prohibits aliases, floating/tag/package contracts, label rechecks, local schema substitutes, and live execution while disabled (ADR-009, ADR-013, FR-RES-01). |
| `.github/workflows/real-codex-cli-demo.yml` | REMOVE | Historical certification invoked Codex through a second trigger; certification is not the organization target path. Removal eliminates unintended duplicate execution. |
| `.github/workflows/user-idea-codex-cli-demo.yml` | REMOVE | Historical user generation published to a sibling repository, contrary to FR-WS-01 and the repository boundary, and duplicated execution/publication. |
| `.github/workflows/release.yml` | REMOVE | Automated package/tag/release behavior is outside this slice and belongs after human review; it is not required by any included ID. |
| `.github/workflows/ci.yml` | MODIFY | CI remains read-only and hermetic. Its required test guards the disabled current interface, the historical “golden MVP” certification job is removed, and wheel verification no longer invokes a legacy CLI. |
| `tests/test_issue_to_codex_workflow.py`, `tests/test_mvp_release_workflow.py`, `tests/test_mvp_workflow_security.py`, `tests/test_user_idea_mvp_workflow.py` | REMOVE | These tests enforced deleted v2.1, manual Codex, sibling-publication, certification, or release workflows. `tests/test_next_mvp_convergence.py` replaces them with fail-closed single-interface invariants. |
| `README.md` | MODIFY | It now points to one disabled future adapter and states that no implementation is supported; historical demos, release, CLI, and full-SDLC paths are no longer presented as current. |
| `pyproject.toml` console script `slugger = "cli.main:main"` | REMOVE | The script exposed legacy MVP build/publish plus experimental router, approval, and orchestration paths as an installed interface. No active next-MVP requirement defines a local CLI (IF-03 is not selected). |
| `mvp/**`, `cli/**`, remaining `tests/test_mvp_*.py`, `tests/mvp/**` | DEFER | These implement and regress the historical v0.1.x local generation/certification design. ADR-010 leaves retain/extract/remove open; they remain non-installed blueprints and cannot be triggered by a supported workflow. They are not conformance evidence. |
| `agents/**`, `orchestrator/**`, `workflow/**`, `providers/**`, `state_machine/**`, `materializer/**`, `memory/**`, and their tests/recipes | DEFER | Multi-agent/full-SDLC/provider-substitution behavior maps to deferred FR-LCM-01/02 and FR-EXT-01. ADR-010 requires quarantine and leaves final extraction/removal open. |
| approval, readiness, release, Canva, consulting, prompt-task, example, and repository-prep material | DEFER | These are historical, experimental, longer-term, or preparatory content. They have no supported entry point; accountable owners must decide later extraction/removal rather than silently promoting them. |
| `docs/mvp.md`, `docs/mvp-release-checklist.md`, `docs/mvp-certification.md`, `docs/codex-demo.md`, `docs/production-readiness.md`, `docs/issue-to-codex-bridge.md` | KEEP (historical) | Their existing status notices preserve history/background. `README.md` no longer routes users to them as operating instructions; Git history rather than compatibility paths preserves removed triggers. |
| Local organization contract schemas/fixtures | KEEP ABSENT | ADR-009 requires direct consumption from the exact external SHA. Searches confirm no second authoritative schema or fixture was introduced locally. |

## Single-path invariant after migration

Only `.github/workflows/codex-execute.yml` represents the next-MVP target interface.
It is reusable (not manually dispatchable), read-only, and unconditionally fails
closed. No workflow calls Codex, creates a branch/PR, publishes to a sibling,
creates a release, or uses a mutable cross-repository reference. Retained source is
blueprint inventory only and has no installed console entry point.

## External dependencies blocking further implementation

The organization owner must implement the canonical result receiver, publish and
approve a new immutable full-SHA release, complete executable `TC-MVP-CI-001`
inputs/expected outputs, and enable the registry after local evidence. Until then,
Slugger cannot claim live delivery or full shared-fixture conformance. ADR-010's
open retain/extract/remove decision blocks treating wholesale deletion of research
code as an authoritative requirement, but does not block its present quarantine.
