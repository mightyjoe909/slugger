# Slugger

Slugger is the execution and product-generation boundary in the Young Consultations
AI-assisted delivery system. The authoritative product direction is
[`docs/VISION.md`](docs/VISION.md); [`AI_CONTEXT.md`](AI_CONTEXT.md) defines the
required reading order and implementation policy.

## Current next-MVP status

The one current target is the organization next-MVP adapter described by
[`docs/next-mvp.md`](docs/next-mvp.md). It will accept the pinned organization
release 2.2.0 `ai-sdlc-contract/v2` request, execute only an authorized task in this
repository, produce at most one validated managed draft pull request, and send one
canonical result.

**The adapter is implemented but is not enabled, certified, or live.** The merged
organization baseline now supplies the immutable compatibility/capability contract,
executable fixture oracle, and canonical result receiver. Current target activation
is separate mutable control-plane state enforced by the organization router;
Slugger neither records nor enforces historical enabled state. The single `.github/workflows/codex-execute.yml` now provides the canonical
admission, verify, implement, managed-draft, and result-delivery path; there is no
parallel disabled adapter. There is currently no supported local CLI, manual Codex demo, publication,
certification, release, or full-SDLC execution path.

The immutable external compatibility unit is:

```text
Young-Consultations/.github@c6090e5bbadcc2102a1cb91875466e9decdada1e
contract: ai-sdlc-contract/v2
fixture manifest: TC-MVP-CI-001
```

Canonical schemas remain owned by the organization control plane and are not copied
into this repository. See [`docs/shared-contract-orchestration.md`](docs/shared-contract-orchestration.md)
for the subordinate integration summary.

## Repository contents

Existing Python MVP, CLI, multi-agent, provider, publication, approval, release,
and full-SDLC modules and their tests are retained only as quarantined historical
or experimental blueprints. They are not installed as a console command, are not
called by the target workflow, and do not establish supported behavior or
next-MVP conformance. [`docs/mvp.md`](docs/mvp.md) is explicitly historical and
[`docs/production-readiness.md`](docs/production-readiness.md) is longer-term
background.

The repository-wide disposition and migration record is
[`docs/next-mvp-migration.md`](docs/next-mvp-migration.md).

## Development checks

Normal CI is hermetic: it has read-only repository permission and does not call
Codex or mutate GitHub branches or pull requests. Blueprint regression tests remain
to detect accidental code decay while extraction/removal decisions are deferred;
they are not next-MVP acceptance or certification evidence.

```bash
pip install -c constraints-ci.txt -e ".[test]"
ruff check .
ruff format --check .
python -m mypy mvp cli
pytest tests/
python -m build
git diff --check
```

## Responsibility boundary

Slugger does not own portfolio intent, priority, or approval; organization
contracts, routing, registration, compatibility, or result receiving; human
review or merge; release, deployment, or production decisions; or sibling
repository implementation. Automation will end at a draft pull request and a
canonical result. Local implementation and conformance do not enable the target;
activation remains an organization control-plane decision.

See [`CONTRIBUTING.md`](CONTRIBUTING.md), [`SECURITY.md`](SECURITY.md), and
[`docs/mvp-merge-governance.md`](docs/mvp-merge-governance.md) before contributing.
