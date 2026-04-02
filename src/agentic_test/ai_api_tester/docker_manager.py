"""Allow-listed Docker Compose operations only (no arbitrary shell)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from agentic_test.ai_api_tester.config import HarnessSettings, StackProfile
from agentic_test.ai_api_tester.errors import DockerComposeError
from agentic_test.ai_api_tester.paths import find_repo_root


def _compose_file(repo_root: Path, settings: HarnessSettings) -> Path:
    cf = repo_root / settings.compose_filename
    if not cf.is_file():
        msg = f"Compose file not found: {cf.name}"
        raise DockerComposeError(msg)
    return cf


def start_target_stack(
    profile: StackProfile,
    *,
    repo_root: Path | None = None,
    settings: HarnessSettings | None = None,
    timeout_s: float = 300.0,
) -> dict[str, Any]:
    """Run allow-listed `docker compose up` for mongo-only or full profile."""
    root = repo_root or find_repo_root()
    cfg = settings or HarnessSettings()
    if profile not in cfg.allowed_compose_profiles:
        msg = f"Profile must be one of {cfg.allowed_compose_profiles}."
        raise DockerComposeError(msg)
    _compose_file(root, cfg)
    cmd: list[str]
    if profile == "mongo":
        cmd = ["docker", "compose", "-f", str(root / cfg.compose_filename), "up", "-d", "mongo"]
    else:
        cmd = [
            "docker",
            "compose",
            "-f",
            str(root / cfg.compose_filename),
            "--profile",
            "full",
            "up",
            "-d",
            "--build",
        ]
    proc = subprocess.run(
        cmd,
        cwd=root,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "")[-500:]
        raise DockerComposeError(f"docker compose up failed: {tail}")
    return {
        "ok": True,
        "profile": profile,
        "command": cmd,
        "stdout_tail": (proc.stdout or "")[-2000:],
        "stderr_tail": (proc.stderr or "")[-2000:],
    }


def stop_target_stack(
    *,
    repo_root: Path | None = None,
    settings: HarnessSettings | None = None,
    timeout_s: float = 120.0,
) -> dict[str, Any]:
    """Run `docker compose down` for the approved compose file only."""
    root = repo_root or find_repo_root()
    cfg = settings or HarnessSettings()
    _compose_file(root, cfg)
    cmd = ["docker", "compose", "-f", str(root / cfg.compose_filename), "down"]
    proc = subprocess.run(
        cmd,
        cwd=root,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "")[-500:]
        raise DockerComposeError(f"docker compose down failed: {tail}")
    return {
        "ok": True,
        "command": cmd,
        "stdout_tail": (proc.stdout or "")[-2000:],
        "stderr_tail": (proc.stderr or "")[-2000:],
    }
