"""FastAPI dependencies for database access."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from pymongo import MongoClient
from pymongo.database import Database

from agentic_test.config import Settings, get_settings
from agentic_test.microblog.repository import MessageRepository


def get_mongo_client(request: Request) -> MongoClient:
    return request.app.state.mongo_client


def get_database(
    client: Annotated[MongoClient, Depends(get_mongo_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Database:
    return client[settings.mongodb_database]


def get_message_repository(
    db: Annotated[Database, Depends(get_database)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> MessageRepository:
    return MessageRepository(db, settings.messages_collection)
