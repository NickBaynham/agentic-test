"""MongoDB persistence for microblog messages."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.collection import Collection
from pymongo.database import Database

from agentic_test.microblog.schemas import MessageCreate, MessageUpdate, SortField, SortOrder


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _doc_to_public(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(doc["_id"]),
        "author_first_name": doc["author_first_name"],
        "author_last_name": doc["author_last_name"],
        "author_email": doc["author_email"],
        "text": doc["text"],
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }


class MessageRepository:
    def __init__(self, db: Database, collection_name: str) -> None:
        self._col: Collection = db[collection_name]

    def create(self, data: MessageCreate) -> dict[str, Any]:
        now = _utcnow()
        doc = {
            "author_first_name": data.author_first_name,
            "author_last_name": data.author_last_name,
            "author_email": str(data.author_email),
            "text": data.text,
            "created_at": now,
            "updated_at": now,
        }
        result = self._col.insert_one(doc)
        stored = self._col.find_one({"_id": result.inserted_id})
        assert stored is not None
        return _doc_to_public(stored)

    def get_by_id(self, message_id: str) -> dict[str, Any] | None:
        try:
            oid = ObjectId(message_id)
        except InvalidId:
            return None
        doc = self._col.find_one({"_id": oid})
        if doc is None:
            return None
        return _doc_to_public(doc)

    def list_messages(
        self,
        *,
        skip: int,
        limit: int,
        sort_by: SortField,
        sort_order: SortOrder,
    ) -> tuple[list[dict[str, Any]], int]:
        direction = DESCENDING if sort_order == SortOrder.desc else ASCENDING
        sort_key = sort_by.value
        total = self._col.count_documents({})
        cursor = (
            self._col.find({}).sort(sort_key, direction).skip(skip).limit(limit)
        )
        items = [_doc_to_public(d) for d in cursor]
        return items, total

    def delete(self, message_id: str) -> bool:
        try:
            oid = ObjectId(message_id)
        except InvalidId:
            return False
        result = self._col.delete_one({"_id": oid})
        return result.deleted_count == 1

    def update(self, message_id: str, data: MessageUpdate) -> dict[str, Any] | None:
        try:
            oid = ObjectId(message_id)
        except InvalidId:
            return None
        patch: dict[str, Any] = {}
        if data.author_first_name is not None:
            patch["author_first_name"] = data.author_first_name
        if data.author_last_name is not None:
            patch["author_last_name"] = data.author_last_name
        if data.author_email is not None:
            patch["author_email"] = str(data.author_email)
        if data.text is not None:
            patch["text"] = data.text
        if not patch:
            existing = self._col.find_one({"_id": oid})
            if existing is None:
                return None
            return _doc_to_public(existing)
        patch["updated_at"] = _utcnow()
        result = self._col.find_one_and_update(
            {"_id": oid},
            {"$set": patch},
            return_document=ReturnDocument.AFTER,
        )
        if result is None:
            return None
        return _doc_to_public(result)
