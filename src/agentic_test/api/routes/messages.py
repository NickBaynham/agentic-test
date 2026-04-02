"""REST routes for microblog messages."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from agentic_test.microblog.deps import get_message_repository
from agentic_test.microblog.repository import MessageRepository
from agentic_test.microblog.schemas import (
    MessageCreate,
    MessageListResponse,
    MessagePublic,
    MessageUpdate,
    SortField,
    SortOrder,
)

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post(
    "",
    response_model=MessagePublic,
    status_code=status.HTTP_201_CREATED,
)
def create_message(
    body: MessageCreate,
    repo: Annotated[MessageRepository, Depends(get_message_repository)],
) -> MessagePublic:
    doc = repo.create(body)
    return MessagePublic.model_validate(doc)


@router.get("/{message_id}", response_model=MessagePublic)
def get_message(
    message_id: str,
    repo: Annotated[MessageRepository, Depends(get_message_repository)],
) -> MessagePublic:
    doc = repo.get_by_id(message_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return MessagePublic.model_validate(doc)


@router.get("", response_model=MessageListResponse)
def list_messages(
    repo: Annotated[MessageRepository, Depends(get_message_repository)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    sort_by: SortField = Query(default=SortField.created_at),
    sort_order: SortOrder = Query(default=SortOrder.desc),
) -> MessageListResponse:
    items, total = repo.list_messages(
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return MessageListResponse(
        items=[MessagePublic.model_validate(i) for i in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    message_id: str,
    repo: Annotated[MessageRepository, Depends(get_message_repository)],
) -> None:
    ok = repo.delete(message_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")


@router.patch("/{message_id}", response_model=MessagePublic)
def update_message(
    message_id: str,
    body: MessageUpdate,
    repo: Annotated[MessageRepository, Depends(get_message_repository)],
) -> MessagePublic:
    doc = repo.update(message_id, body)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return MessagePublic.model_validate(doc)
