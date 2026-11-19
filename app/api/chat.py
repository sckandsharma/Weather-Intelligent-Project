from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.security import limiter
from app.database.models import Conversation, Feedback, Message, User
from app.database.session import get_db
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationDetailResponse,
    ConversationListItem,
    FeedbackCreate,
    FeedbackResponse,
    MessageHistoryItem,
    PaginatedConversations,
)
from app.services.chat_service import process_chat_message

router = APIRouter(tags=["chat"])


@router.post("/chat/ask", response_model=ChatResponse, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def ask_chat(
    request: Request,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    return await process_chat_message(
        user_id=current_user.id,
        message=payload.message,
        db=db,
        conversation_id=payload.conversation_id,
    )


@router.get("/chat/history", status_code=status.HTTP_200_OK)
def get_chat_history(
    conversation_id: int | None = Query(default=None, description="Specific conversation ID to view messages"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    if conversation_id is not None:
        conv = db.get(Conversation, conversation_id)
        if not conv or conv.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found",
            )

        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
            .limit(limit)
            .offset(offset)
        )
        messages = db.execute(stmt).scalars().all()

        return ConversationDetailResponse(
            conversation_id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            messages=[
                MessageHistoryItem(
                    id=m.id,
                    question=m.question,
                    answer=m.answer,
                    created_at=m.created_at,
                )
                for m in messages
            ],
        )

    total_count = db.scalar(
        select(func.count(Conversation.id)).where(Conversation.user_id == current_user.id)
    ) or 0

    stmt = (
        select(
            Conversation.id,
            Conversation.title,
            Conversation.created_at,
            func.count(Message.id).label("message_count"),
        )
        .outerjoin(Message, Conversation.id == Message.conversation_id)
        .where(Conversation.user_id == current_user.id)
        .group_by(Conversation.id)
        .order_by(Conversation.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = db.execute(stmt).all()

    items = [
        ConversationListItem(
            id=r.id,
            title=r.title,
            created_at=r.created_at,
            message_count=r.message_count,
        )
        for r in rows
    ]

    return PaginatedConversations(
        items=items,
        total=total_count,
        limit=limit,
        offset=offset,
    )


@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    payload: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FeedbackResponse:
    message = db.get(Message, payload.message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message {payload.message_id} not found",
        )

    if message.conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot submit feedback for a conversation belonging to another user",
        )

    existing_feedback = db.scalar(
        select(Feedback).where(Feedback.message_id == payload.message_id)
    )
    if existing_feedback:
        existing_feedback.rating = payload.rating
        existing_feedback.comments = payload.comments.strip() if payload.comments else None
        db.commit()
        db.refresh(existing_feedback)
        return FeedbackResponse(
            id=existing_feedback.id,
            message_id=existing_feedback.message_id,
            rating=existing_feedback.rating,
            comments=existing_feedback.comments,
            status="updated",
        )

    feedback = Feedback(
        message_id=payload.message_id,
        rating=payload.rating,
        comments=payload.comments.strip() if payload.comments else None,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return FeedbackResponse(
        id=feedback.id,
        message_id=feedback.message_id,
        rating=feedback.rating,
        comments=feedback.comments,
        status="recorded",
    )
