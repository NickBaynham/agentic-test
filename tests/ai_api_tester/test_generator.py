"""Generator output must always be valid Python (any scenario text)."""

from __future__ import annotations

import ast

import pytest

from agentic_test.ai_api_tester.generator import build_playwright_api_test_module


@pytest.mark.parametrize(
    "scenario",
    [
        'Verify "GET /health" returns JSON',
        "It's the health check",
        'Mixed \'single\' and "double" quotes',
        'Triple """ in text',
        "Line1\nLine2",
        r"path\file",
        "",
    ],
)
def test_generated_module_parses(scenario: str) -> None:
    _, src = build_playwright_api_test_module(
        scenario=scenario,
        endpoint="/health",
        http_method="GET",
        expected_status=200,
        response_json_keys=["status"],
    )
    ast.parse(src)


def test_generation_scenario_constant_round_trip() -> None:
    scenario = 'Say "hello" to GET /health'
    _, src = build_playwright_api_test_module(
        scenario=scenario,
        endpoint="/health",
        http_method="GET",
        expected_status=200,
    )
    tree = ast.parse(src)
    assigns = [n for n in tree.body if isinstance(n, ast.Assign)]
    assert assigns, "expected _GENERATION_SCENARIO assignment"
    # First assignment after module docstring should bind scenario
    names = [t.id for t in assigns[0].targets if isinstance(t, ast.Name)]
    assert "_GENERATION_SCENARIO" in names
