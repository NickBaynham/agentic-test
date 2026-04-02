"""JUnit / summary parsing."""

from __future__ import annotations

from pathlib import Path

from agentic_test.ai_api_tester.result_parser import build_run_summary, parse_junit_xml


def test_parse_junit_minimal(tmp_path: Path) -> None:
    p = tmp_path / "j.xml"
    p.write_text(
        """<?xml version="1.0"?>
<testsuite name="suite" tests="1" failures="0" errors="0">
  <testcase name="test_ok" classname="t" time="0.01"/>
</testsuite>
""",
        encoding="utf-8",
    )
    out = parse_junit_xml(p)
    assert out["ok"] is True
    assert out["totals"]["passed"] == 1
    assert out["cases"][0]["status"] == "passed"


def test_build_run_summary(tmp_path: Path) -> None:
    junit = tmp_path / "j.xml"
    junit.write_text(
        """<?xml version="1.0"?>
<testsuite name="suite" tests="1" failures="0" errors="0">
  <testcase name="test_ok" classname="t" time="0.01"/>
</testsuite>
""",
        encoding="utf-8",
    )
    s = build_run_summary(
        returncode=0,
        stdout="ok",
        stderr="",
        junit_path=junit,
        json_report_path=None,
    )
    assert s["passed"] is True
    assert s["exit_code"] == 0
