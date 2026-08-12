# Interface Contract — `Young-Consultations/.github` control plane

This interface is aligned, without a cross-repository conformance claim, to
organization release 2.2.0 at
`Young-Consultations/.github@c6090e5bbadcc2102a1cb91875466e9decdada1e`, payload
`ai-sdlc-contract/v2`, and fixture manifest `TC-MVP-CI-001`. See the complete
[next-MVP baseline](../next-mvp.md).

## Ownership and authority

The organization control plane owns canonical contracts, registry, admission,
routing, and result receipt. Only canonical task status `approved` is router
admissible; `queued` is not authorization, and material change requires a new
`task_id` and approval. Slugger authenticates the admitted caller and validates the
payload and local policy. It is not an approval authority and must not require or
recheck `ai-sdlc-approved`, another label, or a repository-specific approval record.
Rich approval provenance is deferred to v3.

The immutable target-capability entry targets `Young-Consultations/slugger`,
permits `automation`, `bug-fix`, `documentation`, `feature`, and `testing`, requires
`ai-sdlc-contract/v2` and `draft_pr_only: true`, and declares `delivery_id`,
`ai-sdlc-delivery-id`, and `duplicate-reused` as branch identity, ownership marker,
and terminal reuse status. Capability does not encode current activation. Mutable
enabled/disabled state is router-owned and enforced before dispatch; Slugger does
not consume or enforce historical activation state from the compatibility pin.

## Inbound reusable-workflow contract

`.github/workflows/codex-execute.yml` must accept exactly these required strings:

* `execution_input_json`: the complete canonical `execution-input/v2` object;
* `concurrency_group`: the routing-path transport concurrency identity.

`execution_input` is obsolete. Neither an artifact alternative, a live issue-label
lookup, sibling-repository access, an undocumented module/package, nor control-plane
credentials are part of the target contract. `concurrency_group` is validated and
used, but `delivery_id` is the only idempotency key; retries retain it.

Slugger validates with format checking against the immutable schema at
`https://raw.githubusercontent.com/Young-Consultations/.github/c6090e5bbadcc2102a1cb91875466e9decdada1e/contracts/execution-input.schema.json`.
It likewise consumes the pinned `task-contract.schema.json` and
`execution-result.schema.json` directly. Slugger defines no local canonical enum,
schema fork, or extension, and assumes no published package.

## Result contract

Slugger validates canonical `execution-result/v2`, preserves the input
`delivery_id`, `correlation_id`, and target, and separately calls:

```text
Young-Consultations/.github/.github/workflows/codex-result-receiver.yml@c6090e5bbadcc2102a1cb91875466e9decdada1e
```

The receiver inputs are `execution_result` and `source_issue`; its secret is
`CODEX_RESULT_TOKEN`; its outputs are `accepted`, `delivery_id`, `correlation_id`,
`execution_status`, `failure_category`, and `diagnostic_summary`. It is the
organization-owned implemented receiver for this compatibility baseline. Slugger
must not build a competing receiver. Transport acknowledgement is not execution
success, receiver credentials remain isolated to result delivery, and failed
transport preserves the immutable canonical result for safe redelivery.

## Delivery, publication, and failures

Routing is at least once. Identical redelivery converges on idempotent visible
effects; changed content under a delivery ID is rejected. `correlation_id` is for
observability only. Implement publication is limited to one managed open draft per
delivery in this repository. Ownership ambiguity fails closed, matching work is
reused, and a create race is requeried. Verify makes no Codex call or mutation and
returns canonical `verified` with schema-required null publication fields.

Every accepted, rejected, blocked, or failed terminal path produces a sanitized
canonical result when trusted identity is available. Identical result redelivery is
safe; conflicting redelivery fails closed. No target operation merges, releases,
deploys, performs production operations, or touches another repository.

## Version, activation, and conformance

All workflow and schema references use the full SHA. `main`, a mutable tag, and an
assumed package are prohibited dependencies. `TC-MVP-CI-001` supplies executable
inputs and expected results and remains the semantic oracle; Slugger-specific tests
may extend local policy coverage but cannot redefine organization expectations.
Conformance uses fakes and creates no real Codex, branch, or pull-request effect.
Passing conformance does not enable Slugger: mutable activation remains exclusively
owned by the organization router.
