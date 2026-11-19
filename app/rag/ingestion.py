from io import BytesIO
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET
import zipfile
from bs4 import BeautifulSoup
from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Document, DocumentChunk
from app.rag.chunking import split_text_into_chunks
from app.rag.embeddings import generate_embeddings

SUPPORTED_EXTENSIONS = {".pdf", ".html", ".htm", ".docx", ".txt", ".md"}


def _extract_pdf_bytes(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)


def _extract_html_bytes(content: bytes) -> str:
    soup = BeautifulSoup(content.decode("utf-8", errors="ignore"), "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    return soup.get_text(separator="\n")


def _extract_docx_bytes(content: bytes) -> str:
    with zipfile.ZipFile(BytesIO(content)) as archive:
        xml_bytes = archive.read("word/document.xml")
    tree = ET.fromstring(xml_bytes)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []
    for para in tree.findall(".//w:p", ns):
        parts = [node.text for node in para.findall(".//w:t", ns) if node.text]
        if parts:
            paragraphs.append("".join(parts))
    return "\n\n".join(paragraphs)


def extract_text_from_bytes(filename: str, content: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format '{ext}'. Supported formats: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    if ext == ".pdf":
        return _extract_pdf_bytes(content)
    if ext in {".html", ".htm"}:
        return _extract_html_bytes(content)
    if ext == ".docx":
        return _extract_docx_bytes(content)
    return content.decode("utf-8", errors="ignore")


def extract_text_from_file(file_path: str | Path) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return extract_text_from_bytes(path.name, path.read_bytes())


def ingest_text(
    db: Session,
    title: str,
    source_url: str,
    category: str,
    raw_text: str,
    version: str = "1.0",
    source_file: str | None = None,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> dict[str, Any]:
    existing = db.scalar(
        select(Document).where(
            Document.title == title,
            Document.version == version,
        )
    )
    if existing:
        return {
            "document_id": existing.id,
            "title": existing.title,
            "version": existing.version,
            "chunks_created": 0,
            "status": "already_exists",
        }

    chunks = split_text_into_chunks(
        raw_text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    if not chunks:
        raise ValueError("No extractable text found in document")

    embeddings = generate_embeddings(chunks)

    try:
        document = Document(
            title=title.strip(),
            source_url=source_url.strip(),
            category=category.strip().lower(),
            version=version.strip(),
        )
        db.add(document)
        db.flush()

        chunk_records = []
        for idx, (chunk_text, vector) in enumerate(zip(chunks, embeddings)):
            chunk_records.append(
                DocumentChunk(
                    document_id=document.id,
                    chunk_text=chunk_text,
                    embedding=vector,
                    chunk_metadata={
                        "chunk_index": idx,
                        "total_chunks": len(chunks),
                        "char_length": len(chunk_text),
                        "category": document.category,
                        "version": document.version,
                        "source_file": source_file,
                    },
                )
            )

        db.add_all(chunk_records)
        db.commit()
        db.refresh(document)

        return {
            "document_id": document.id,
            "title": document.title,
            "version": document.version,
            "chunks_created": len(chunk_records),
            "status": "ingested",
        }
    except Exception:
        db.rollback()
        raise


def ingest_file(
    db: Session,
    file_path: str | Path,
    title: str,
    source_url: str,
    category: str,
    version: str = "1.0",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> dict[str, Any]:
    path = Path(file_path)
    raw_text = extract_text_from_file(path)
    return ingest_text(
        db=db,
        title=title,
        source_url=source_url,
        category=category,
        raw_text=raw_text,
        version=version,
        source_file=path.name,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )


def ingest_uploaded_bytes(
    db: Session,
    filename: str,
    content: bytes,
    title: str,
    source_url: str,
    category: str,
    version: str = "1.0",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> dict[str, Any]:
    raw_text = extract_text_from_bytes(filename, content)
    return ingest_text(
        db=db,
        title=title,
        source_url=source_url,
        category=category,
        raw_text=raw_text,
        version=version,
        source_file=filename,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )