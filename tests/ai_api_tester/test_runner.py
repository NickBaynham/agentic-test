"""Pytest runner wrapper."""

from __future__ import annotations

from pathlib import Path

from agentic_test.ai_api_tester.config import HarnessSettings
from agentic_test.ai_api_tester.runner import run_pytest_targets


def test_run_pytest_trivial_file(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\nversion='0'\n", encoding="utf-8")
    t = tmp_path / "test_trivial.py"
    t.write_text("def test_ok():\n    assert 1 == 1\n", encoding="utf-8")
    cfg = HarnessSettings(
        generated_artifacts_subdir="artifacts/latest",
    )
    (tmp_path / "artifacts" / "latest").mkdir(parents=True)
    summary = run_pytest_targets([t], repo_root=tmp_path, settings=cfg)
    assert summary["passed"] is True
    assert summary["exit_code"] == 0
    assert "junit" in summary
