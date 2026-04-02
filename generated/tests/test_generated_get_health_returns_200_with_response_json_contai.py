"""
Generated API test (Playwright sync APIRequestContext only).

Scenario:
GET /health returns 200 with response JSON containing key status

Endpoint: GET /health
Expected status: 200
Optional JSON keys: ['status']
"""
from __future__ import annotations

import os

import pytest
from playwright.sync_api import sync_playwright

pytestmark = pytest.mark.generated_api

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")


@pytest.fixture(scope="module")
def api_request_context():
    """Playwright APIRequestContext — no browser UI."""
    with sync_playwright() as p:
        ctx = p.request.new_context(base_url=API_BASE_URL)
        yield ctx
        ctx.dispose()


def test_generated_get_health_returns_200_with_response_json_contai(api_request_context):
    """GET /health returns 200 with response JSON containing key status"""
    response = api_request_context.get("/health")
    assert response.status == 200, (
        "Unexpected status "
        f"{response.status} body={response.text()[:500]!r}"
    )

    data = response.json()
    assert "status" in data, f"missing key 'status' in {data!r}"
