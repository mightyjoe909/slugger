"""Repository-specific path and secret validation for generated changes."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ALLOWED_ROOTS = {
    ".ai-sdlc",
    ".github",
    ".gitignore",
    "AI_CONTEXT.md",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "README.md",
    "SECURITY.md",
    "agents",
    "artifacts",
    "benchmarks",
    "cli",
    "config",
    "constraints-ci.txt",
    "conformance",
    "consulting",
    "contracts",
    "core",
    "docker",
    "docs",
    "examples",
    "knowledge",
    "logs",
    "materializer",
    "memory",
    "metrics",
    "models",
    "mvp",
    "observability",
    "orchestrator",
    "plugins",
    "poetry.lock",
    "prompts",
    "providers",
    "pyproject.toml",
    "scripts",
    "services",
    "slugger-generated-demos-README.md",
    "state_machine",
    "templates",
    "tests",
    "validators",
    "workflow",
}
PROTECTED_PATHS = {
    ".ai-sdlc/conformance",
    ".github",
    "AI_CONTEXT.md",
    "SECURITY.md",
    "config/mvp-conformance-pin.json",
    "contracts",
    "scripts/codex_target_adapter.py",
    "scripts/run_tc_mvp_ci_001.py",
    "scripts/test_codex_execute_contract.py",
    "scripts/validate_repository.py",
    "tests/fixtures/mvp-v2",
    "tests/test_conformance.py",
    "tests/test_workflow_contract.py",
}
FORBIDDEN_NAMES = re.compile(
    r"(^|/)(\.env($|\.)|credentials|secrets?($|\.)|.*\.(pem|key)$)", re.IGNORECASE
)
SECRET_VALUE = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9_]{20,}|"
    r"github_pat_[A-Za-z0-9_]{20,})"
)


def run(*args: str) -> str:
    return subprocess.run(args, check=True, text=True, capture_output=True).stdout


def main() -> None:
    entries = run(
        "git", "status", "--porcelain=v1", "-z", "--untracked-files=all"
    ).split("\0")
    files: list[str] = []
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if not entry:
            continue
        if len(entry) < 4 or entry[2] != " ":
            raise SystemExit("git returned malformed candidate status")
        name = entry[3:]
        files.append(name)
        if entry[0] in "RC" or entry[1] in "RC":
            if index >= len(entries) or not entries[index]:
                raise SystemExit("git returned malformed rename status")
            files.append(entries[index])
            index += 1
    for name in files:
        path = Path(name)
        if path.is_absolute() or ".." in path.parts:
            raise SystemExit("a changed path escapes the repository")
        root = path.parts[0]
        if root not in ALLOWED_ROOTS:
            raise SystemExit(
                f"changed path is outside the repository allowlist: {name}"
            )
        if any(
            name == protected or name.startswith(protected + "/")
            for protected in PROTECTED_PATHS
        ):
            raise SystemExit(f"candidate modified protected execution policy: {name}")
        if FORBIDDEN_NAMES.search(name):
            raise SystemExit("a credential-like file name was detected")
        if path.is_symlink():
            raise SystemExit(f"candidate created a symbolic link: {name}")

    # Scan both working-tree and index changes. Codex may stage a tracked file,
    # in which case the default diff no longer contains its generated content.
    def added_content(diff: str) -> str:
        return "\n".join(
            line[1:]
            for line in diff.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        )

    content = added_content(run("git", "diff", "--no-ext-diff"))
    content += "\n" + added_content(run("git", "diff", "--cached", "--no-ext-diff"))
    untracked_files = set(
        run("git", "ls-files", "--others", "--exclude-standard").splitlines()
    )
    for name in files:
        path = Path(name)
        if path.is_file() and name in untracked_files:
            content += path.read_text(encoding="utf-8", errors="replace")
    if SECRET_VALUE.search(content):
        raise SystemExit("a credential-like value was detected in generated content")


if __name__ == "__main__":
    main()
