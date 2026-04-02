import os
from pathlib import Path

import pytest

from agentic_test.main import _project_root, load_environment


def test_project_root_contains_pyproject():
    root = _project_root()
    assert (root / "pyproject.toml").is_file()


def test_load_environment_reads_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    fake_pkg = tmp_path / "src" / "agentic_test"
    fake_pkg.mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n", encoding="utf-8")
    monkeypatch.setattr(
        "agentic_test.main.__file__",
        str(fake_pkg / "main.py"),
    )
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)
    (tmp_path / ".env").write_text("APP_ENV=test\nDEBUG=true\n", encoding="utf-8")
    try:
        load_environment()
        assert os.environ.get("APP_ENV") == "test"
        assert os.environ.get("DEBUG") == "true"
    finally:
        os.environ.pop("APP_ENV", None)
        os.environ.pop("DEBUG", None)
