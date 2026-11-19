from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Conversation, Document, DocumentChunk, EvaluationResult, Message, User, UserRole
from app.auth.jwt_handler import create_access_token


def test_conversation_ownership_isolation(client: TestClient, db: Session, regular_user: User):
    # User B
    user_b = User(
        full_name="User B",
        email=f"user_b_{datetime.now(timezone.utc).timestamp()}@example.com",
        password_hash="hash",
        role=UserRole.USER,
        is_active=True,
    )
    db.add(user_b)
    db.flush()

    # Create conversation for User B
    conv_b = Conversation(user_id=user_b.id, title="User B Private Conversation")
    db.add(conv_b)
    db.flush()

    msg_b = Message(conversation_id=conv_b.id, question="Private Q", answer="Private A")
    db.add(msg_b)
    db.commit()

    # User A tries to view User B's conversation
    token_a = create_access_token(user_id=regular_user.id, role=regular_user.role.value)
    headers_a = {"Authorization": f"Bearer {token_a}"}

    res = client.get(f"/api/v1/chat/history?conversation_id={conv_b.id}", headers=headers_a)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_message_persistence_and_pagination(client: TestClient, db: Session, regular_user: User, user_headers):
    conv = Conversation(user_id=regular_user.id, title="Pagination Test")
    db.add(conv)
    db.flush()

    for i in range(15):
        db.add(Message(conversation_id=conv.id, question=f"Q{i}", answer=f"A{i}"))
    db.commit()

    res = client.get(f"/api/v1/chat/history?conversation_id={conv.id}&limit=5&offset=0", headers=user_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["messages"]) == 5
    assert data["messages"][0]["question"] == "Q0"


def test_evaluation_result_persistence(db: Session):
    res_row = EvaluationResult(
        run_id="run_test_db_123",
        test_case_id="test_1",
        routing_score=1.0,
        retrieval_score=0.95,
        answer_score=0.90,
        latency_ms=185.0,
    )
    db.add(res_row)
    db.commit()
    db.refresh(res_row)

    saved = db.scalar(select(EvaluationResult).where(EvaluationResult.run_id == "run_test_db_123"))
    assert saved is not None
    assert saved.routing_score == 1.0
    assert saved.retrieval_score == 0.95


def test_vector_similarity_returns_closest_first(db: Session):
    doc = Document(title="Vector Math Doc", source_url="https://example.com", category="test", version="1.0")
    db.add(doc)
    db.flush()

    # Chunk A: vector pointing along dimension 0
    vec_a = [0.0] * 384
    vec_a[0] = 1.0

    # Chunk B: vector pointing along dimension 1
    vec_b = [0.0] * 384
    vec_b[1] = 1.0

    db.add(DocumentChunk(document_id=doc.id, chunk_text="Chunk A", embedding=vec_a, chunk_metadata={"name": "A"}))
    db.add(DocumentChunk(document_id=doc.id, chunk_text="Chunk B", embedding=vec_b, chunk_metadata={"name": "B"}))
    db.commit()

    # Query vector close to Chunk A
    query_vec = [0.0] * 384
    query_vec[0] = 0.95
    query_vec[1] = 0.05

    stmt = (
        select(DocumentChunk)
        .where(DocumentChunk.document_id == doc.id)
        .order_by(DocumentChunk.embedding.cosine_distance(query_vec).asc())
        .limit(2)
    )
    results = db.execute(stmt).scalars().all()

    assert len(results) == 2
    assert results[0].chunk_text == "Chunk A"
    assert results[1].chunk_text == "Chunk B"
