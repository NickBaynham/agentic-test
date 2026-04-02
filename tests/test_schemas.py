"""Unit tests for Pydantic message schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from agentic_test.microblog.schemas import MessageCreate, MessageUpdate


def test_message_create_accepts_valid_payload():
    m = MessageCreate(
        author_first_name="Ada",
        author_last_name="Lovelace",
        author_email="ada@example.com",
        text="Hello, world!",
    )
    assert m.text == "Hello, world!"


def test_message_create_rejects_text_over_255():
    with pytest.raises(ValidationError):
        MessageCreate(
            author_first_name="A",
            author_last_name="B",
            author_email="a@b.co",
            text="x" * 256,
        )


def test_message_create_strips_whitespace():
    m = MessageCreate(
        author_first_name="  Ada  ",
        author_last_name=" Lovelace ",
        author_email="ada@example.com",
        text=" hi ",
    )
    assert m.author_first_name == "Ada"
    assert m.author_last_name == "Lovelace"
    assert m.text == "hi"


def test_message_update_empty_strings_become_none():
    u = MessageUpdate(author_first_name="   ")
    assert u.author_first_name is None


def test_message_update_partial():
    u = MessageUpdate(text="only text")
    assert u.text == "only text"
    assert u.author_email is None
