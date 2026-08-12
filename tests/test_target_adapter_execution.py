from mvp.target_adapter.adapter import TargetAdapter
from mvp.target_adapter.contract import validate_request
from mvp.target_adapter.ownership import ManagedPullRequest, marker
from tests.test_target_adapter_contract import SCHEMA, payload


class Repo:
    def __init__(self):
        self.prs = []
        self.published = 0

    def pull_requests(self):
        return self.prs

    def branch_exists(self, branch):
        return False

    def publish(self, r, branch):
        self.published += 1
        pr = ManagedPullRequest(
            1, "https://example/pr/1", "open", True, branch, "main", marker(r)
        )
        self.prs.append(pr)
        return pr


def request(mode="implement"):
    p = payload()
    p["mode"] = mode
    return validate_request(
        p,
        schema=SCHEMA,
        concurrency_group="group",
        caller_repository="Young-Consultations/.github",
    )


def test_verify_has_zero_effects():
    calls = []
    repo = Repo()
    result = TargetAdapter(
        repo, lambda r: calls.append("codex"), lambda r: calls.append("validation")
    ).execute(request("verify"))
    assert result["execution_status"] == "verified"
    assert calls == [] and repo.published == 0


def test_implement_and_duplicate():
    calls = []
    repo = Repo()
    adapter = TargetAdapter(
        repo, lambda r: calls.append("codex"), lambda r: calls.append("validation")
    )
    assert adapter.execute(request())["execution_status"] == "succeeded"
    assert adapter.execute(request())["execution_status"] == "duplicate-reused"
    assert calls == ["codex", "validation"] and repo.published == 1


def test_codex_failure():
    def fail(r):
        raise RuntimeError("provider secret sk-not-shown")

    result = TargetAdapter(Repo(), fail, lambda r: None).execute(request())
    assert result["execution_status"] == "failed"
    assert "sk-not-shown" not in result["diagnostic_summary"]


def test_validation_failure_and_publication_failure():
    def bad(r):
        raise RuntimeError("tests failed")

    assert (
        TargetAdapter(Repo(), lambda r: None, bad).execute(request())[
            "failure_category"
        ]
        == "execution"
    )
    repo = Repo()
    repo.publish = lambda r, b: (_ for _ in ()).throw(RuntimeError("publish failed"))
    assert (
        TargetAdapter(repo, lambda r: None, lambda r: None).execute(request())[
            "execution_status"
        ]
        == "failed"
    )


def test_timeout():
    def timeout(r):
        raise TimeoutError("deadline")

    assert (
        TargetAdapter(Repo(), timeout, lambda r: None).execute(request())[
            "failure_category"
        ]
        == "timeout"
    )
