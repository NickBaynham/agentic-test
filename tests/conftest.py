"""Global test setup: MongoDB is mocked unless integration tests opt into a real server."""

from __future__ import annotations

import os

import mongomock
import pymongo
import pytest


def pytest_configure(config) -> None:
    """Run before test collection so `mongomock` is used when the API module imports `MongoClient`."""
    os.environ.setdefault("MONGODB_PING_ON_STARTUP", "false")
    pymongo.MongoClient = mongomock.MongoClient  # type: ignore[misc, assignment]


@pytest.fixture(autouse=True)
def _drop_microblog_database_after_test():
    yield
    try:
        from agentic_test.api.app import app

        client = app.state.mongo_client
    except AttributeError:
        return
    from agentic_test.config import get_settings

    db_name = get_settings().mongodb_database
    client.drop_database(db_name)
