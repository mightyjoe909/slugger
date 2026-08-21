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
| `.github/workflows/codex-execute.yml` | MODIFY | It is the sole target entry point (FR-INT-01/02), now exposes only `workflow_dispatch` with required strings `execution_input_json` and `concurrency_group`, invokes the one repository adapter, and calls only the planned 2.3.1 receiver. Target-side historical activation enforcement is prohibited. |
| Obsolete `workflow_call`, artifact/run-ID inputs, v2.1 tag/package checkout, target-side label approval, locally constructed result, and target-supplied receiver trust | REMOVE | The issue #135 recovery architecture prohibits incompatible triggers, aliases, floating/package assumptions, label rechecks, schema substitutes, target-owned journal trust, and target-side activation enforcement (ADR-009, ADR-013, ADR-015, FR-RES-01). |
| `.github/workflows/real-codex-cli-demo.yml` | REMOVE | Historical certification invoked Codex through a second trigger; certification is not the organization target path. Removal eliminates unintended duplicate execution. |
| `.github/workflows/user-idea-codex-cli-demo.yml` | REMOVE | Historical user generation published to a sibling repository, contrary to FR-WS-01 and the repository boundary, and duplicated execution/publication. |
| `.github/workflows/release.yml` | REMOVE | Automated package/tag/release behavior is outside this slice and belongs after human review; it is not required by any included ID. |
| `.github/workflows/ci.yml` | MODIFY | CI remains read-only and hermetic. It now guards the single canonical adapter, exact shared/target pin, activation separation, complete 29-scenario evidence, credential boundaries, package verification, and action syntax. |
| `tests/test_issue_to_codex_workflow.py`, `tests/test_mvp_release_workflow.py`, `tests/test_mvp_workflow_security.py`, `tests/test_user_idea_mvp_workflow.py` | REMOVE | These tests enforced deleted v2.1, manual Codex, sibling-publication, certification, or release workflows. `tests/test_next_mvp_convergence.py` replaces them with fail-closed single-interface invariants. |
| `README.md` | MODIFY | It must point to one canonical future adapter, the new immutable baseline, and router-owned mutable activation; historical demos, release, CLI, and full-SDLC paths are no longer presented as current. |
| `pyproject.toml` console script `slugger = "cli.main:main"` | REMOVE | The script exposed legacy MVP build/publish plus experimental router, approval, and orchestration paths as an installed interface. No active next-MVP requirement defines a local CLI (IF-03 is not selected). |
| `mvp/codex_target.py`, `tests/test_canonical_delivery_idempotency.py` | REMOVE | These are useful ownership/idempotency blueprints but accept aliases and noncanonical contract shapes, recheck source approval, and define local marker/branch semantics. Retaining them beside the v2 adapter would create a competing organization contract path. Migrate only mechanics that match the pinned oracle. |
| `mvp/target_adapter/**` and its tests | REMOVE | The package validated an obsolete nested payload, local result vocabulary, vendored historic schemas, `workflow_call`, and credential-bearing publication path. `scripts/codex_target_adapter.py` is now the single adapter seam; Git history preserves the discarded blueprint. |
| `scripts/codex_target_adapter.py`, `scripts/test_codex_execute_contract.py`, `scripts/run_tc_mvp_ci_001.py`, `tests/test_conformance.py`, `tests/test_workflow_contract.py` | ADD | These provide exact schema/format/caller validation, immutable delivery binding, branch-plus-PR reconciliation before Codex and after create races, canonical result mapping, security/transport regressions, and the complete organization oracle with ten zero-effect traps. |
| Remaining `mvp/**`, `cli/**`, `tests/test_mvp_*.py`, `tests/mvp/**` | DEFER | These implement and regress the historical v0.1.x local generation/certification design. ADR-010 leaves retain/extract/remove open; they remain non-installed blueprints and cannot be triggered by a supported workflow. They are not conformance evidence. |
| `agents/**`, `orchestrator/**`, `workflow/**`, `providers/**`, `state_machine/**`, `materializer/**`, `memory/**`, and their tests/recipes | DEFER | Multi-agent/full-SDLC/provider-substitution behavior maps to deferred FR-LCM-01/02 and FR-EXT-01. ADR-010 requires quarantine and leaves final extraction/removal open. |
| approval, readiness, release, Canva, consulting, prompt-task, example, and repository-prep material | DEFER | These are historical, experimental, longer-term, or preparatory content. They have no supported entry point; accountable owners must decide later extraction/removal rather than silently promoting them. |
| `docs/mvp.md`, `docs/mvp-release-checklist.md`, `docs/mvp-certification.md`, `docs/codex-demo.md`, `docs/production-readiness.md`, `docs/issue-to-codex-bridge.md` | KEEP (historical) | Their existing status notices preserve history/background. `README.md` no longer routes users to them as operating instructions; Git history rather than compatibility paths preserves removed triggers. |
| `contracts/*.schema.json`, `tests/fixtures/mvp-v2/*`, `config/mvp-conformance-pin.json`, `.ai-sdlc/conformance/tc-mvp-ci-001.json` | ADD AS PINNED EVIDENCE | Exact byte-identical shared blobs at `e27b8a5` support hermetic validation. The non-recursive pin binds them with exact target files; they are validation inputs and evidence, never a local contract fork or production-readiness claim. |

## Single-path invariant after migration

Only `.github/workflows/codex-execute.yml` represents the next-MVP target interface.
It is dynamically dispatchable with exactly two inputs and delegates all target
behavior to one pinned adapter. Retained blueprint source remains outside the
supported adapter path.

## Reassessed implementation readiness

The recovery candidate supplies exact schemas and executable `TC-MVP-CI-001`
inputs/expected results; the repository adapter and zero-effect report are now
implemented. Remaining gates are review/merge, immutable adapter tagging, registry
tag/commit/report binding, publication/live verification of the planned 2.3.1
receiver, credential confirmation, final compatibility release, and one-at-a-time
review-state validation. Current activation is separate mutable organization-router
state. Passing local conformance must not enable Slugger.
