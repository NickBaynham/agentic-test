"""Unit tests for sandbox path resolution."""

from __future__ import annotations

import pytest

from agentic_test.ai_api_tester.errors import SandboxError
from agentic_test.ai_api_tester.paths import (
    find_repo_root,
    resolve_repo_relative,
)


def test_find_repo_root() -> None:
    root = find_repo_root()
    assert (root / "pyproject.toml").is_file()


def test_resolve_repo_relative_rejects_traversal() -> None:
    root = find_repo_root()
    with pytest.raises(SandboxError):
        resolve_repo_relative(root, "..")
    with pytest.raises(SandboxError):
        resolve_repo_relative(root, "foo/../../etc/passwd")


def test_resolve_repo_relative_rejects_absolute() -> None:
    root = find_repo_root()
    with pytest.raises(SandboxError):
        resolve_repo_relative(root, "/etc/passwd")
