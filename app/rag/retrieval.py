from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Document, DocumentChunk
from app.rag.embeddings import generate_embedding


def retrieve_relevant_chunks(
    query: str,
    db: Session,
    top_k: int = 5,
    min_score: float = 0.3,
    category_filter: str | None = None,
) -> list[dict[str, Any]]:
    cleaned_query = query.strip()
    if not cleaned_query or top_k <= 0:
        return []

    query_vector = generate_embedding(cleaned_query)
    distance_expr = DocumentChunk.embedding.cosine_distance(query_vector)
    max_distance = 1.0 - min_score

    stmt = (
        select(DocumentChunk, Document, distance_expr.label("distance"))
        .join(Document, DocumentChunk.document_id == Document.id)
        .where(distance_expr <= max_distance)
    )

    if category_filter:
        stmt = stmt.where(Document.category == category_filter.strip().lower())

    stmt = stmt.order_by(distance_expr.asc()).limit(top_k)
    rows = db.execute(stmt).all()

    results: list[dict[str, Any]] = []
    for chunk, document, distance in rows:
        similarity = max(0.0, min(1.0, 1.0 - float(distance)))
        metadata = chunk.chunk_metadata or {}
        results.append(
            {
                "chunk_id": chunk.id,
                "document_id": document.id,
                "chunk_text": chunk.chunk_text,
                "document_title": document.title,
                "source_url": document.source_url,
                "category": document.category,
                "chunk_index": metadata.get("chunk_index"),
                "similarity_score": round(similarity, 4),
            }
        )

    return results