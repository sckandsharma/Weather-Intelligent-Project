from typing import Any
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_admin
from app.database.models import Document, DocumentChunk, User
from app.database.session import get_db
from app.rag.ingestion import SUPPORTED_EXTENSIONS, ingest_uploaded_bytes

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    source_url: str = Form(...),
    category: str = Form(...),
    version: str = Form("1.0"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> dict[str, Any]:
    filename = file.filename or "uploaded_document"
    ext = f".{filename.split('.')[-1].lower()}" if "." in filename else ""

    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    try:
        result = ingest_uploaded_bytes(
            db=db,
            filename=filename,
            content=content,
            title=title.strip(),
            source_url=source_url.strip(),
            category=category.strip().lower(),
            version=version.strip(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest document: {str(e)}",
        )

    if result.get("status") == "already_exists":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Document '{title}' (version {version}) already exists in knowledge base",
        )

    return result


@router.get("/", status_code=status.HTTP_200_OK)
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    stmt = (
        select(
            Document.id,
            Document.title,
            Document.source_url,
            Document.category,
            Document.version,
            Document.created_at,
            func.count(DocumentChunk.id).label("chunk_count"),
        )
        .outerjoin(DocumentChunk, Document.id == DocumentChunk.document_id)
        .group_by(Document.id)
        .order_by(Document.created_at.desc())
    )

    rows = db.execute(stmt).all()
    return [
        {
            "id": row.id,
            "title": row.title,
            "source_url": row.source_url,
            "category": row.category,
            "version": row.version,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "chunk_count": row.chunk_count,
        }
        for row in rows
    ]


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> dict[str, str]:
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found",
        )

    db.delete(document)
    db.commit()
    return {"message": f"Document '{document.title}' and all its chunks successfully deleted"}
