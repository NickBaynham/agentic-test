"""Repository root discovery and sandbox path resolution."""

from __future__ import annotations

from pathlib import Path

from agentic_test.ai_api_tester.config import HarnessSettings
from agentic_test.ai_api_tester.errors import SandboxError


def find_repo_root(start: Path | None = None) -> Path:
    """Locate repository root by finding pyproject.toml."""
    here = (start or Path(__file__).resolve()).parent
    for parent in [here, *here.parents]:
        if (parent / "pyproject.toml").is_file():
            return parent
    msg = "Could not locate repository root (pyproject.toml not found)."
    raise SandboxError(msg)


def _resolve_strict(child: Path, root: Path) -> Path:
    root_r = root.resolve()
    resolved = child.resolve()
    try:
        resolved.relative_to(root_r)
    except ValueError as e:
        msg = "Path escapes repository sandbox."
        raise SandboxError(msg) from e
    return resolved


def resolve_repo_relative(repo_root: Path, relative: str) -> Path:
    """Resolve a path relative to repo root; reject traversal."""
    if not relative or relative.startswith("/"):
        msg = "Path must be a relative repository path."
        raise SandboxError(msg)
    if ".." in Path(relative).parts:
        msg = "Path traversal is not allowed."
        raise SandboxError(msg)
    return _resolve_strict(repo_root / relative, repo_root)


def ensure_under(
    repo_root: Path,
    path: Path,
    allowed_root: Path,
) -> Path:
    """Ensure path resolves inside allowed_root (both under repo)."""
    ar = _resolve_strict(allowed_root, repo_root)
    p = _resolve_strict(path, repo_root)
    try:
        p.relative_to(ar)
    except ValueError as e:
        msg = "Path is outside the allowed workspace directory."
        raise SandboxError(msg) from e
    return p


def generated_tests_dir(repo_root: Path, settings: HarnessSettings) -> Path:
    return _resolve_strict(repo_root / settings.generated_tests_subdir, repo_root)


def generated_history_dir(repo_root: Path, settings: HarnessSettings) -> Path:
    return _resolve_strict(repo_root / settings.generated_history_subdir, repo_root)


def artifacts_dir(repo_root: Path, settings: HarnessSettings) -> Path:
    return _resolve_strict(repo_root / settings.generated_artifacts_subdir, repo_root)


def meta_dir(repo_root: Path, settings: HarnessSettings) -> Path:
    return _resolve_strict(repo_root / settings.generated_meta_subdir, repo_root)


def handwritten_tests_dir(repo_root: Path, settings: HarnessSettings) -> Path:
    return _resolve_strict(repo_root / settings.handwritten_tests_subdir, repo_root)
