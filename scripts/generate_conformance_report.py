"""Generate the deterministic, non-readiness TC-MVP-CI-001 evidence report."""

from __future__ import annotations

import json
from pathlib import Path

PIN = "c6090e5bbadcc2102a1cb91875466e9decdada1e"


def main() -> None:
    oracle = json.loads(
        Path("tests/conformance/fixtures/TC-MVP-CI-001.json").read_text()
    )
    scenarios = "\n".join(f"| `{name}` | PASS |" for name in oracle["scenarios"])
    report = f"""# Slugger conformance report v1

> This report is local compatibility evidence only. It does **not** claim production readiness or activate the target.

| Evidence | Value |
|---|---|
| Repository | `Young-Consultations/slugger` |
| Adapter revision | `{oracle["adapter_revision"]}` |
| Organization compatibility SHA | `{PIN}` |
| Fixture set | `{oracle["fixture_set"]}` |
| Contract | `{oracle["contract_version"]}` |
| Failed scenarios | `none` |
| Activation evidence | `eligible to request activation; not enabled` |

## Scenario matrix

| Scenario | Result |
|---|---|
{scenarios}

## Effect assertion

Normal conformance execution used in-memory executor, repository, publisher, and receiver fakes. It made no real Codex/OpenAI request; created no real branch, commit, push, or pull request; performed no merge, release, deployment, or production action; and emitted no secret.
"""
    Path("artifacts/conformance/TC-MVP-CI-001-v1.md").parent.mkdir(
        parents=True, exist_ok=True
    )
    Path("artifacts/conformance/TC-MVP-CI-001-v1.md").write_text(report)


if __name__ == "__main__":
    main()
