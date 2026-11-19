from sqlalchemy.orm import Session

from app.database.models import Document, DocumentChunk
from app.rag.chunking import clean_text, split_text_into_chunks
from app.rag.ingestion import ingest_text
from app.rag.retrieval import retrieve_relevant_chunks


def test_chunking_boundaries_and_overlap():
    sample_text = (
        "The India Meteorological Department issues color coded warnings. "
        "Green alert indicates normal weather with no disruptions. "
        "Yellow alert advises citizens to watch and stay updated. "
        "Orange alert requires people to be prepared for severe disruptions. "
        "Red alert demands immediate action during extreme disaster situations."
    )
    chunks = split_text_into_chunks(sample_text, chunk_size=120, chunk_overlap=30)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) <= 150
        assert len(chunk) > 0


def test_clean_text_normalization():
    dirty = "   Multiple   spaces   and \r\n weird \t\t tabs.   "
    cleaned = clean_text(dirty)
    assert "Multiple spaces and" in cleaned
    assert "weird tabs." in cleaned


def test_ingest_text_and_database_persistence(db: Session):
    title = "Test Flood Safety Handbook"
    url = "https://ndma.gov.in/test-flood"
    cat = "rain_flood"
    text_content = (
        "During flash floods, turn around and do not drown. "
        "Six inches of rapidly moving water can knock down an adult. "
        "Twelve inches of water can float and sweep away passenger cars."
    )

    result = ingest_text(
        db=db,
        title=title,
        source_url=url,
        category=cat,
        raw_text=text_content,
        version="1.0",
        chunk_size=150,
        chunk_overlap=30,
    )

    assert result["status"] == "ingested"
    assert result["chunks_created"] >= 1
    doc_id = result["document_id"]

    # Verify rows in DB
    doc = db.get(Document, doc_id)
    assert doc is not None
    assert doc.title == title
    assert doc.category == cat

    chunks = db.query(DocumentChunk).where(DocumentChunk.document_id == doc_id).all()
    assert len(chunks) == result["chunks_created"]
    for c in chunks:
        assert len(c.embedding) == 384
        assert c.chunk_metadata["category"] == cat


def test_retrieval_similarity_threshold_and_citations(db: Session):
    title = "Thunderstorm Safety Protocol"
    url = "https://ndma.gov.in/thunderstorm"
    text_content = (
        "Follow the 30-30 rule for lightning. If thunder follows lightning in less than 30 seconds, "
        "seek indoor shelter immediately and avoid open fields, tall trees, or swimming pools."
    )
    ingest_text(
        db=db,
        title=title,
        source_url=url,
        category="rain_flood",
        raw_text=text_content,
        version="1.0",
    )

    # Relevant query -> returns matching chunk with verified citations
    matches = retrieve_relevant_chunks("What is the 30-30 rule for lightning?", db=db, top_k=2, min_score=0.40)
    assert len(matches) >= 1
    top_match = matches[0]
    assert top_match["document_title"] == title
    assert top_match["source_url"] == url
    assert "30-30" in top_match["chunk_text"]
    assert top_match["similarity_score"] >= 0.40

    # Completely unrelated query -> should return 0 chunks due to min_score threshold
    unrelated = retrieve_relevant_chunks("How to prepare Italian pasta recipe?", db=db, top_k=2, min_score=0.75)
    assert len(unrelated) == 0
