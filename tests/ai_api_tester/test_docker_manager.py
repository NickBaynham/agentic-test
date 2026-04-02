"""Docker manager allow-list (mocked)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agentic_test.ai_api_tester.docker_manager import start_target_stack
from agentic_test.ai_api_tester.errors import DockerComposeError


def test_start_rejects_unknown_profile(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\nversion='0'\n", encoding="utf-8")
    (tmp_path / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    with pytest.raises(DockerComposeError):
        start_target_stack("bogus", repo_root=tmp_path)  # type: ignore[arg-type]


def test_start_mongo_calls_compose(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\nversion='0'\n", encoding="utf-8")
    (tmp_path / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    proc = MagicMock()
    proc.returncode = 0
    proc.stdout = "ok"
    proc.stderr = ""
    with patch(
        "agentic_test.ai_api_tester.docker_manager.subprocess.run",
        return_value=proc,
    ) as run:
        out = start_target_stack("mongo", repo_root=tmp_path)
    assert out["ok"] is True
    cmd = run.call_args[0][0]
    assert cmd[:4] == ["docker", "compose", "-f", str(tmp_path / "docker-compose.yml")]
