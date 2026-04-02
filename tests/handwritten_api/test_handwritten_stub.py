"""
Handwritten API-style tests (read-only for MCP `update_generated_test`).

These illustrate patterns for Playwright `APIRequestContext`. They are skipped unless
`API_BASE_URL` is set so local `pytest` runs stay hermetic.
"""

from __future__ import annotations

import os

import pytest
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.handwritten_api]

API_BASE_URL = os.environ.get("API_BASE_URL", "")


@pytest.mark.skipif(not API_BASE_URL, reason="Set API_BASE_URL to run against a live API")
def test_handwritten_health_probe() -> None:
    with sync_playwright() as p:
        ctx = p.request.new_context(base_url=API_BASE_URL)
        try:
            r = ctx.get("/health")
            assert r.status == 200
            body = r.json()
            assert "status" in body
        finally:
            ctx.dispose()
