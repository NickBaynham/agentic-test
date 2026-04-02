"""Sandboxed read/write for generated tests and safe reads elsewhere."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agentic_test.ai_api_tester.config import HarnessSettings
from agentic_test.ai_api_tester.errors import HandwrittenEditError, SandboxError
from agentic_test.ai_api_tester.paths import (
    artifacts_dir,
    ensure_under,
    generated_history_dir,
    generated_tests_dir,
    handwritten_tests_dir,
    meta_dir,
    resolve_repo_relative,
)


def is_generated_test_path(repo_root: Path, path: Path, settings: HarnessSettings) -> bool:
    g = generated_tests_dir(repo_root, settings)
    try:
        path.resolve().relative_to(g)
    except ValueError:
        return False
    return path.suffix == ".py"


def is_handwritten_test_path(repo_root: Path, path: Path, settings: HarnessSettings) -> bool:
    h = handwritten_tests_dir(repo_root, settings)
    if not h.is_dir():
        return False
    try:
        path.resolve().relative_to(h)
    except ValueError:
        return False
    return path.suffix == ".py"


def read_allowed_test_file(repo_root: Path, relative_path: str, settings: HarnessSettings) -> Path:
    """Resolve a repo-relative path that must fall under generated or handwritten API tests."""
    p = resolve_repo_relative(repo_root, relative_path)
    g = generated_tests_dir(repo_root, settings)
    h = handwritten_tests_dir(repo_root, settings)
    if p.is_file() and is_generated_test_path(repo_root, p, settings):
        return ensure_under(repo_root, p, g)
    if h.is_dir() and p.is_file() and is_handwritten_test_path(repo_root, p, settings):
        return ensure_under(repo_root, p, h)
    msg = "File is not a readable API test under generated/ or tests/handwritten_api/."
    raise SandboxError(msg)


def write_generated_test(
    repo_root: Path,
    relative_path: str,
    content: str,
    settings: HarnessSettings,
    *,
    metadata: dict[str, Any] | None = None,
) -> Path:
    """Write only under generated/tests; optional sidecar metadata in .meta/."""
    p = resolve_repo_relative(repo_root, relative_path)
    g = generated_tests_dir(repo_root, settings)
    ensure_under(repo_root, p, g)
    if p.suffix != ".py":
        msg = "Generated tests must be .py files."
        raise SandboxError(msg)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    if metadata is not None:
        mdir = meta_dir(repo_root, settings)
        mdir.mkdir(parents=True, exist_ok=True)
        sidecar = mdir / f"{p.stem}.json"
        sidecar.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return p


def update_generated_test_content(
    repo_root: Path,
    relative_path: str,
    new_content: str,
    settings: HarnessSettings,
) -> Path:
    p = resolve_repo_relative(repo_root, relative_path)
    if not is_generated_test_path(repo_root, p, settings):
        if is_handwritten_test_path(repo_root, p, settings):
            raise HandwrittenEditError("Refusing to edit handwritten tests.")
        msg = "Path must be a generated test under generated/tests/."
        raise SandboxError(msg)
    g = generated_tests_dir(repo_root, settings)
    ensure_under(repo_root, p, g)
    hist = generated_history_dir(repo_root, settings)
    hist.mkdir(parents=True, exist_ok=True)
    if p.exists():
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        backup = hist / f"{ts}_{p.name}"
        shutil.copy2(p, backup)
    p.write_text(new_content, encoding="utf-8")
    return p


def delete_generated_test(repo_root: Path, relative_path: str, settings: HarnessSettings) -> None:
    p = resolve_repo_relative(repo_root, relative_path)
    if not is_generated_test_path(repo_root, p, settings):
        msg = "Only generated tests under generated/tests/ may be deleted."
        raise SandboxError(msg)
    g = generated_tests_dir(repo_root, settings)
    ensure_under(repo_root, p, g)
    if p.is_file():
        p.unlink()
    meta = meta_dir(repo_root, settings) / f"{p.stem}.json"
    if meta.is_file():
        meta.unlink()


def list_test_files(repo_root: Path, settings: HarnessSettings) -> tuple[list[Path], list[Path]]:
    gen = generated_tests_dir(repo_root, settings)
    gen.mkdir(parents=True, exist_ok=True)
    generated = sorted(gen.glob("test_*.py")) if gen.is_dir() else []
    hand_root = handwritten_tests_dir(repo_root, settings)
    handwritten = sorted(hand_root.glob("test_*.py")) if hand_root.is_dir() else []
    return handwritten, generated


def ensure_artifacts_dir(repo_root: Path, settings: HarnessSettings) -> Path:
    a = artifacts_dir(repo_root, settings)
    a.mkdir(parents=True, exist_ok=True)
    return a
