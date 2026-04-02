"""Structured summaries from pytest artifacts (JUnit XML + optional JSON report)."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, cast


def parse_junit_xml(path: Path) -> dict[str, Any]:
    """Parse pytest-emitted JUnit XML into a compact summary."""
    if not path.is_file():
        return {"ok": False, "detail": "JUnit file missing."}
    tree = ET.parse(path)
    root = tree.getroot()
    if root.tag == "testsuites":
        suites = list(root)
    elif root.tag == "testsuite":
        suites = [root]
    else:
        return {"ok": False, "detail": "Unexpected JUnit root element."}
    cases: list[dict[str, Any]] = []
    total_fail = 0
    total_error = 0
    total_pass = 0
    for suite in suites:
        for case in suite.findall("testcase"):
            name = case.attrib.get("name", "")
            classname = case.attrib.get("classname", "")
            failure = case.find("failure")
            error = case.find("error")
            skipped = case.find("skipped")
            status = "passed"
            message = ""
            if failure is not None:
                status = "failed"
                total_fail += 1
                message = (failure.attrib.get("message") or failure.text or "")[:2000]
            elif error is not None:
                status = "error"
                total_error += 1
                message = (error.attrib.get("message") or error.text or "")[:2000]
            elif skipped is not None:
                status = "skipped"
            else:
                total_pass += 1
            cases.append(
                {
                    "name": name,
                    "classname": classname,
                    "status": status,
                    "message": message,
                },
            )
    return {
        "ok": True,
        "totals": {
            "passed": total_pass,
            "failed": total_fail,
            "error": total_error,
            "cases": len(cases),
        },
        "cases": cases,
    }


def load_json_report(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if isinstance(raw, dict):
        return cast(dict[str, Any], raw)
    return None


def build_run_summary(
    *,
    returncode: int,
    stdout: str,
    stderr: str,
    junit_path: Path,
    json_report_path: Path | None = None,
) -> dict[str, Any]:
    """Combine subprocess outcome with parsed artifacts."""
    junit_summary = parse_junit_xml(junit_path)
    extra = load_json_report(json_report_path) if json_report_path else None
    passed = (
        returncode == 0
        and junit_summary.get("ok")
        and junit_summary.get("totals", {}).get(
            "failed",
            0,
        )
        == 0
        and junit_summary.get("totals", {}).get("error", 0) == 0
    )
    return {
        "passed": passed,
        "exit_code": returncode,
        "stdout_tail": stdout[-8000:],
        "stderr_tail": stderr[-8000:],
        "junit": junit_summary,
        "json_report": extra,
    }
