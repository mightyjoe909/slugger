# Shared-contract orchestration — next-MVP target slice

[`docs/next-mvp.md`](next-mvp.md) is the normative Slugger baseline. The immutable
compatibility unit is organization release 2.2.0,
`Young-Consultations/.github@c6090e5bbadcc2102a1cb91875466e9decdada1e`, contract
payload `ai-sdlc-contract/v2`, and executable fixture oracle `TC-MVP-CI-001`.

The reusable target entry point accepts required strings `execution_input_json`
(the complete canonical execution-input object) and `concurrency_group` (transport
concurrency identity). `delivery_id`, not the concurrency group or an Actions run
ID, is the idempotency and deterministic ownership identity. At-least-once retries
preserve it. A changed payload under an existing delivery ID is rejected.

Canonical task, execution-input, and execution-result schemas are consumed directly
from `contracts/task-contract.schema.json`, `contracts/execution-input.schema.json`,
and `contracts/execution-result.schema.json` at the full SHA above. No package,
floating reference, local schema, enum, fork, or compatibility-derived activation
state is part of the MVP target interface.

Immutable compatibility defines protocol and target-capability semantics. Mutable
activation is separate organization control-plane state enforced by the router
before dispatch. Slugger authenticates the admitted caller and enforces exact
target, contract, schema/format, task type, mode, draft-only, delivery, ownership,
and repository-local policy, but it neither reads historical enabled state nor
rechecks a live source label or approval.

Implement mode reconciles the deterministic delivery branch and organization-owned
PR marker before mutation. It reuses one exact matching managed draft, fails closed
on ambiguity, and requeries after a create race. Verify mode has no Codex, branch,
PR, or publication effect.

Slugger sends canonical results separately to
`Young-Consultations/.github/.github/workflows/codex-result-receiver.yml@c6090e5bbadcc2102a1cb91875466e9decdada1e`.
Acknowledgement is transport state, not execution success. Result credentials are
isolated from Codex and target publication; identical redelivery is safe and a
conflicting result fails closed. Slugger does not create a competing receiver.

`TC-MVP-CI-001` supplies executable inputs and expected results. Slugger consumes
that oracle without redefining its semantics and keeps genuinely local target-policy
tests separate. Normal conformance CI injects fakes and makes no real Codex call,
branch, commit, push, pull request, or receiver mutation. Passing local conformance
does not activate the target.
