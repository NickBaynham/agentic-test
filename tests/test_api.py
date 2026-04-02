"""API tests against FastAPI with mongomock (see tests/conftest.py)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from agentic_test.api.app import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


def test_root_serves_swagger_ui(client: TestClient):
    r = client.get("/")
    assert r.status_code == 200
    assert "swagger" in r.text.lower() or "openapi" in r.text.lower()


def test_openapi_json_available(client: TestClient):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    assert spec["info"]["title"] == "Microblog API"
    assert "/messages" in spec["paths"]


def test_health(client: TestClient):
    assert client.get("/health").json() == {"status": "ok"}


def test_create_list_get_patch_delete_flow(client: TestClient):
    create = client.post(
        "/messages",
        json={
            "author_first_name": "Alan",
            "author_last_name": "Turing",
            "author_email": "alan@example.com",
            "text": "We can only see a short distance ahead.",
        },
    )
    assert create.status_code == 201
    mid = create.json()["id"]

    one = client.get(f"/messages/{mid}")
    assert one.status_code == 200
    assert one.json()["author_email"] == "alan@example.com"

    listed = client.get("/messages?limit=10&sort_by=created_at&sort_order=desc")
    assert listed.status_code == 200
    body = listed.json()
    assert body["total"] >= 1
    assert any(m["id"] == mid for m in body["items"])

    patched = client.patch(f"/messages/{mid}", json={"text": "Updated."})
    assert patched.status_code == 200
    assert patched.json()["text"] == "Updated."

    deleted = client.delete(f"/messages/{mid}")
    assert deleted.status_code == 204

    assert client.get(f"/messages/{mid}").status_code == 404


def test_get_unknown_returns_404(client: TestClient):
    assert client.get("/messages/507f1f77bcf86cd799439011").status_code == 404
