"""Smoke test MCP app factory (stdio server not started)."""

from __future__ import annotations

from agentic_test.ai_api_tester.server import build_mcp_app


def test_build_mcp_app() -> None:
    app = build_mcp_app()
    assert app is not None
