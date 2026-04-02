"""HTTP introspection for health and OpenAPI (httpx, no browser)."""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import httpx

from agentic_test.ai_api_tester.config import HarnessSettings


def fetch_health(
    base_url: str,
    settings: HarnessSettings,
    *,
    timeout_s: float = 10.0,
) -> dict[str, Any]:
    """GET health endpoint; return structured result without raising on HTTP errors."""
    url = urljoin(base_url.rstrip("/") + "/", settings.health_path.lstrip("/"))
    try:
        with httpx.Client(timeout=timeout_s) as client:
            r = client.get(url)
    except httpx.HTTPError as e:
        return {
            "reachable": False,
            "error": type(e).__name__,
            "detail": "Transport error when calling health endpoint.",
        }
    body_preview: str
    try:
        body_preview = r.text[:2000]
    except Exception:  # noqa: BLE001
        body_preview = ""
    return {
        "reachable": True,
        "status_code": r.status_code,
        "body_preview": body_preview,
    }


def fetch_openapi_json(
    base_url: str,
    settings: HarnessSettings,
    *,
    timeout_s: float = 30.0,
) -> dict[str, Any]:
    """Fetch OpenAPI JSON from the target service."""
    url = urljoin(base_url.rstrip("/") + "/", settings.openapi_path.lstrip("/"))
    try:
        with httpx.Client(timeout=timeout_s) as client:
            r = client.get(url)
    except httpx.HTTPError as e:
        return {
            "ok": False,
            "error": type(e).__name__,
            "detail": "Transport error when fetching OpenAPI.",
        }
    if r.status_code != 200:
        return {
            "ok": False,
            "status_code": r.status_code,
            "body_preview": r.text[:1000],
        }
    try:
        data = r.json()
    except Exception:  # noqa: BLE001
        return {
            "ok": False,
            "detail": "Response was not valid JSON.",
            "body_preview": r.text[:1000],
        }
    return {"ok": True, "openapi": data, "source_url": url}
