"""Workspace sandbox and generated-file rules."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentic_test.ai_api_tester.config import HarnessSettings
from agentic_test.ai_api_tester.errors import HandwrittenEditError, SandboxError
from agentic_test.ai_api_tester.workspace import (
    delete_generated_test,
    read_allowed_test_file,
    update_generated_test_content,
    write_generated_test,
)


def test_write_and_read_generated(tmp_path: Path) -> None:
    settings = HarnessSettings()
    root = tmp_path / "repo"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\nname='x'\nversion='0'\n", encoding="utf-8")
    rel = "generated/tests/test_gen_x.py"
    write_generated_test(root, rel, "x = 1\n", settings, metadata={"k": "v"})
    p = read_allowed_test_file(root, rel, settings)
    assert p.read_text(encoding="utf-8") == "x = 1\n"
    assert (root / "generated/tests/.meta/test_gen_x.json").is_file()


def test_update_refuses_handwritten(tmp_path: Path) -> None:
    settings = HarnessSettings()
    root = tmp_path / "repo"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\nname='x'\nversion='0'\n", encoding="utf-8")
    hw = root / "tests/handwritten_api"
    hw.mkdir(parents=True)
    hf = hw / "test_hw.py"
    hf.write_text("def test_x(): assert 1\n", encoding="utf-8")
    rel = "tests/handwritten_api/test_hw.py"
    with pytest.raises(HandwrittenEditError):
        update_generated_test_content(root, rel, "bad", settings)


def test_delete_only_generated(tmp_path: Path) -> None:
    settings = HarnessSettings()
    root = tmp_path / "repo"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\nname='x'\nversion='0'\n", encoding="utf-8")
    with pytest.raises(SandboxError):
        delete_generated_test(root, "tests/handwritten_api/test_hw.py", settings)
