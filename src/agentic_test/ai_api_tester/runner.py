"""Allow-listed pytest invocation (no arbitrary subprocess)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from agentic_test.ai_api_tester.config import HarnessSettings
from agentic_test.ai_api_tester.paths import find_repo_root
from agentic_test.ai_api_tester.result_parser import build_run_summary
from agentic_test.ai_api_tester.workspace import ensure_artifacts_dir


def run_pytest_targets(
    targets: list[Path],
    *,
    repo_root: Path | None = None,
    settings: HarnessSettings | None = None,
    extra_env: dict[str, str] | None = None,
    keyword_expression: str | None = None,
    timeout_s: float = 600.0,
) -> dict[str, Any]:
    """Run pytest on explicit paths under the repository."""
    root = repo_root or find_repo_root()
    cfg = settings or HarnessSettings()
    if not targets:
        msg = "At least one pytest target path is required."
        raise ValueError(msg)
    for t in targets:
        t.resolve().relative_to(root.resolve())
    art = ensure_artifacts_dir(root, cfg)
    junit = art / "junit.xml"
    report = art / "pytest-report.json"
    cmd: list[str] = [
        sys.executable,
        "-m",
        "pytest",
        *[str(t) for t in targets],
        "-v",
        "--tb=short",
        f"--junitxml={junit}",
        "--json-report",
        f"--json-report-file={report}",
    ]
    if keyword_expression:
        cmd.extend(["-k", keyword_expression])
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    proc = subprocess.run(
        cmd,
        cwd=root,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        env=env,
        check=False,
    )
    summary = build_run_summary(
        returncode=proc.returncode,
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
        junit_path=junit,
        json_report_path=report,
    )
    summary["artifacts"] = {
        "junit_xml": str(junit.relative_to(root)),
        "json_report": str(report.relative_to(root)),
    }
    return summary
