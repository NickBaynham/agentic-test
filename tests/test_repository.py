"""Unit tests for the MongoDB message repository (in-memory via mongomock)."""

from __future__ import annotations

import mongomock
import pytest

from agentic_test.microblog.repository import MessageRepository
from agentic_test.microblog.schemas import MessageCreate, MessageUpdate, SortField, SortOrder


@pytest.fixture
def repo() -> MessageRepository:
    client = mongomock.MongoClient()
    db = client["test_microblog"]
    return MessageRepository(db, "messages")


def test_create_and_get(repo: MessageRepository):
    created = repo.create(
        MessageCreate(
            author_first_name="Grace",
            author_last_name="Hopper",
            author_email="grace@example.com",
            text="Ship it.",
        )
    )
    got = repo.get_by_id(created["id"])
    assert got is not None
    assert got["text"] == "Ship it."
    assert got["author_email"] == "grace@example.com"


def test_get_invalid_id_returns_none(repo: MessageRepository):
    assert repo.get_by_id("not-an-objectid") is None


def test_list_sort_and_pagination(repo: MessageRepository):
    for i in range(3):
        repo.create(
            MessageCreate(
                author_first_name="U",
                author_last_name=str(i),
                author_email=f"u{i}@example.com",
                text=f"m{i}",
            )
        )
    items, total = repo.list_messages(
        skip=0,
        limit=2,
        sort_by=SortField.created_at,
        sort_order=SortOrder.asc,
    )
    assert total == 3
    assert len(items) == 2


def test_update_message(repo: MessageRepository):
    c = repo.create(
        MessageCreate(
            author_first_name="A",
            author_last_name="B",
            author_email="a@b.co",
            text="old",
        )
    )
    u = repo.update(c["id"], MessageUpdate(text="new"))
    assert u is not None
    assert u["text"] == "new"
    assert u["author_first_name"] == "A"


def test_update_empty_patch_returns_existing(repo: MessageRepository):
    c = repo.create(
        MessageCreate(
            author_first_name="A",
            author_last_name="B",
            author_email="a@b.co",
            text="x",
        )
    )
    u = repo.update(c["id"], MessageUpdate())
    assert u is not None
    assert u["text"] == "x"


def test_delete_message(repo: MessageRepository):
    c = repo.create(
        MessageCreate(
            author_first_name="A",
            author_last_name="B",
            author_email="a@b.co",
            text="bye",
        )
    )
    assert repo.delete(c["id"]) is True
    assert repo.get_by_id(c["id"]) is None
    assert repo.delete(c["id"]) is False
