"""End-to-end harness flow (no LLM): generate Playwright API test, run pytest, parse result."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pytest_httpserver import HTTPServer

from agentic_test.ai_api_tester.handlers import ApiTestHarness

pytestmark = pytest.mark.integration


def test_generate_run_and_parse(httpserver: HTTPServer, tmp_path: Path) -> None:
    pytest.importorskip("playwright.sync_api")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\nversion='0'\n", encoding="utf-8")
    httpserver.expect_request("/health").respond_with_json({"status": "ok"})
    base = httpserver.url_for("/").rstrip("/")

    h = ApiTestHarness(repo_root=tmp_path)
    gen = json.loads(
        h.generate_api_test_from_scenario(
            "probe health endpoint",
            "/health",
            "GET",
            200,
            response_json_keys=["status"],
        ),
    )
    assert gen.get("ok") is True
    rel = gen["relative_path"]
    summary = json.loads(h.run_test(rel, api_base_url=base))
    assert summary.get("passed") is True, summary.get("stderr_tail", "")
