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
| `.github/workflows/codex-execute.yml` | MODIFY | It is the sole eventual entry point (FR-INT-01/02), now limited to required strings `execution_input_json` and `concurrency_group`. The fail-closed stub must now be replaced in place by the single real adapter; target-side historical activation enforcement is prohibited. |
| Obsolete `execution_input_artifact`, `execution_input_run_id`, v2.1 tag/package checkout, target-side label approval, locally constructed result, and direct publication in `codex-execute.yml` | REMOVE | The 2.2.0 baseline prohibits aliases, floating/tag/package contracts, label rechecks, local schema substitutes, and target-side activation enforcement (ADR-009, ADR-013, FR-RES-01). |
| `.github/workflows/real-codex-cli-demo.yml` | REMOVE | Historical certification invoked Codex through a second trigger; certification is not the organization target path. Removal eliminates unintended duplicate execution. |
| `.github/workflows/user-idea-codex-cli-demo.yml` | REMOVE | Historical user generation published to a sibling repository, contrary to FR-WS-01 and the repository boundary, and duplicated execution/publication. |
| `.github/workflows/release.yml` | REMOVE | Automated package/tag/release behavior is outside this slice and belongs after human review; it is not required by any included ID. |
| `.github/workflows/ci.yml` | MODIFY | CI remains read-only and hermetic. Its required tests must guard the single canonical adapter, immutable pin, activation separation, hermetic conformance, and credential boundaries, the historical “golden MVP” certification job is removed, and wheel verification no longer invokes a legacy CLI. |
| `tests/test_issue_to_codex_workflow.py`, `tests/test_mvp_release_workflow.py`, `tests/test_mvp_workflow_security.py`, `tests/test_user_idea_mvp_workflow.py` | REMOVE | These tests enforced deleted v2.1, manual Codex, sibling-publication, certification, or release workflows. `tests/test_next_mvp_convergence.py` replaces them with fail-closed single-interface invariants. |
| `README.md` | MODIFY | It must point to one canonical future adapter, the new immutable baseline, and router-owned mutable activation; historical demos, release, CLI, and full-SDLC paths are no longer presented as current. |
| `pyproject.toml` console script `slugger = "cli.main:main"` | REMOVE | The script exposed legacy MVP build/publish plus experimental router, approval, and orchestration paths as an installed interface. No active next-MVP requirement defines a local CLI (IF-03 is not selected). |
| `mvp/codex_target.py`, `tests/test_canonical_delivery_idempotency.py` | REMOVE | These are useful ownership/idempotency blueprints but accept aliases and noncanonical contract shapes, recheck source approval, and define local marker/branch semantics. Retaining them beside the v2 adapter would create a competing organization contract path. Migrate only mechanics that match the pinned oracle. |
| `mvp/target_adapter/**` | ADD | Add the smallest Slugger-specific adapter package: exact schema/format and caller validation, immutable delivery binding, deterministic managed-draft reconciliation, injected Codex/validation/publication/receiver ports, canonical result mapping, and bounded redaction. It is not a generic cross-repository framework. |
| `tests/test_target_adapter_*.py`, `tests/conformance/test_tc_mvp_ci_001.py` | ADD | Separate Slugger target-policy tests from executable organization-oracle conformance. Fakes must prove zero real Codex, branch, commit, push, PR, or receiver effect. |
| Remaining `mvp/**`, `cli/**`, `tests/test_mvp_*.py`, `tests/mvp/**` | DEFER | These implement and regress the historical v0.1.x local generation/certification design. ADR-010 leaves retain/extract/remove open; they remain non-installed blueprints and cannot be triggered by a supported workflow. They are not conformance evidence. |
| `agents/**`, `orchestrator/**`, `workflow/**`, `providers/**`, `state_machine/**`, `materializer/**`, `memory/**`, and their tests/recipes | DEFER | Multi-agent/full-SDLC/provider-substitution behavior maps to deferred FR-LCM-01/02 and FR-EXT-01. ADR-010 requires quarantine and leaves final extraction/removal open. |
| approval, readiness, release, Canva, consulting, prompt-task, example, and repository-prep material | DEFER | These are historical, experimental, longer-term, or preparatory content. They have no supported entry point; accountable owners must decide later extraction/removal rather than silently promoting them. |
| `docs/mvp.md`, `docs/mvp-release-checklist.md`, `docs/mvp-certification.md`, `docs/codex-demo.md`, `docs/production-readiness.md`, `docs/issue-to-codex-bridge.md` | KEEP (historical) | Their existing status notices preserve history/background. `README.md` no longer routes users to them as operating instructions; Git history rather than compatibility paths preserves removed triggers. |
| Local organization contract schemas/fixtures | KEEP ABSENT | ADR-009 requires direct consumption from the exact external SHA. Searches confirm no second authoritative schema or fixture was introduced locally. |

## Single-path invariant after migration

Only `.github/workflows/codex-execute.yml` represents the next-MVP target interface.
It remains reusable and not manually dispatchable. The implementation task must
replace the unconditional placeholder in place, preserve exactly one target workflow, use only
immutable cross-repository compatibility references, and keep retained blueprint
source outside the supported adapter path.

## Reassessed implementation readiness

The merged compatibility unit supplies the canonical receiver and executable
`TC-MVP-CI-001` inputs/expected results. Current activation is separate mutable
organization-router state and is not a Slugger implementation gate. No genuine
organization-contract blocker remains. The next task should implement one adapter in
`codex-execute.yml`, consume exact organization semantics, add fake-only conformance,
and remove obsolete target behavior rather than retain a disabled parallel path.
Passing local conformance must not enable Slugger.
