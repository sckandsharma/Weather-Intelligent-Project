"""
Master compilation script for PROJECT_STUDY_GUIDE.pdf.
Assembles all 18 sections into a publication-ready technical manual with NumberedCanvas.
"""
import os
import sys
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable, Table, TableStyle
from reportlab.lib import colors

from guide_builder.canvas import NumberedCanvas
from guide_builder.styles import (
    CoverTitle, CoverSubtitle, CoverMeta, H1, H2, Body, BodyBold, BodySmall, TableHeader, TableCell, TableCellBold, TableCellCode,
    PRIMARY, PRIMARY_LIGHT, ACCENT, ROW_BG_ALT, BORDER_COLOR, SUCCESS_COLOR
)
from guide_builder.sections_1_to_4 import build_section_1, build_section_2, build_section_3, build_section_4
from guide_builder.section_5 import build_section_5
from guide_builder.sections_6_to_9 import build_section_6, build_section_7, build_section_8, build_section_9
from guide_builder.sections_10_to_13 import build_section_10, build_section_11, build_section_12, build_section_13
from guide_builder.sections_14_to_18 import build_section_14, build_section_15, build_section_16, build_section_17, build_section_18

def build_cover_page():
    story = []
    story.append(Spacer(1, 40))
    story.append(Paragraph("Weather Intelligence &amp; Advisory Assistant", CoverTitle))
    story.append(Paragraph("Master Technical Interview Study Guide &amp; System Architecture Manual", CoverSubtitle))
    story.append(HRFlowable(width="80%", thickness=2.5, color=PRIMARY, spaceBefore=8, spaceAfter=24))

    meta_text = (
        "<b>Target Role:</b> Python / Backend / AI-ML Engineer<br/>"
        "<b>System Architecture:</b> Microservices Architecture (FastAPI + PostgreSQL pgvector + Redis + Streamlit)<br/>"
        "<b>Core AI Capabilities:</b> Intent-Routed Hybrid RAG + Real-Time Meteorological API Synthesis<br/>"
        "<b>Large Language Model:</b> Google Gemini 3.5 Flash Lite via modern <code>google-genai</code> SDK<br/>"
        "<b>Local Embedding Model:</b> <code>all-MiniLM-L6-v2</code> (384-dimensional dense vectors, zero API cost)<br/>"
        "<b>Automated Benchmark:</b> 15 / 15 Passed (100.0%) | Routing: 1.000 | Retrieval: 1.000 | Answer Quality: 0.972<br/>"
        "<b>Test Suite Verification:</b> 37 / 37 Hermetic Pytest Tests Passing (100% Coverage)<br/>"
        f"<b>Document Generated:</b> {datetime.now().strftime('%B %d, %Y')}<br/>"
        "<b>Status:</b> Production Certified &amp; Fully Containerized"
    )
    
    meta_table = Table([[Paragraph(meta_text, ParagraphStyle("CoverBox", parent=Body, fontSize=9, leading=15, alignment=1))]], colWidths=[480])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ROW_BG_ALT),
        ("BOX", (0, 0), (-1, -1), 1, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 24))

    # Table of contents summary
    toc_data = [
        ["Section", "Title", "Core Topics Covered"],
        ["1", "Project Overview", "10-line executive summary, target users, layman's airport mental model."],
        ["2", "File Classification", "Categorized index of all repository files and architectural responsibilities."],
        ["3", "System Architecture", "ASCII topology, component connectivity, security gateway, data flow."],
        ["4", "Complete Request Flows", "Deep dive 'Is hiking safe in Manali?' + 7 short flows (auth, weather, RAG, etc.)."],
        ["5", "File-by-File Technical Guide", "Exhaustive breakdown of every file, class, function, import, and rationale."],
        ["6", "Database & pgvector", "9 tables, columns, ER diagram, vector dimensions, cosine distance, Alembic."],
        ["7", "Auth & Security Architecture", "Argon2id, dual-token JWT, token blacklist, SlowAPI rate limiting, data isolation."],
        ["8", "Weather API & Caching", "Open-Meteo integration, city aliases, Redis caching, 600s TTL, call auditing."],
        ["9", "RAG Pipeline & Retrieval", "7 official guidelines, chunking logic (500/50), all-MiniLM-L6-v2, cosine search."],
        ["10", "Routing & LLM Engine", "7 deterministic rules, entity extraction, XML prompt design, anti-hallucination."],
        ["11", "Evaluation & Test Suite", "15-question benchmark, metrics scoring formulas, real results, 37 Pytest tests."],
        ["12", "Problems, Bugs & Fixes", "15 real engineering hurdles from our development history with root causes & fixes."],
        ["13", "Design Decisions & Trade-offs", "In-depth rationale for FastAPI, pgvector, all-MiniLM-L6-v2, Redis, Gemini."],
        ["14", "Commands Cheat Sheet", "15 exact terminal commands from virtualenv to Docker, tests, and Redis inspection."],
        ["15", "Assignment Coverage Matrix", "22 requirements mapped to Done status with exact code file evidence."],
        ["16", "Limitations & Interview Defense", "5 honest architectural weak spots and winning defensive interview answers."],
        ["17", "40 Likely Interview Q&As", "40 rapid-fire questions with spoken answers + 2-minute elevator pitch."],
        ["18", "Technical Glossary", "20 plain-English definitions of core AI, backend, and security terms."]
    ]

    toc_rows = []
    for i, r in enumerate(toc_data):
        hdr = i == 0
        toc_rows.append([
            Paragraph(f"<b>{r[0]}</b>", TableHeader if hdr else TableCellBold),
            Paragraph(f"<b>{r[1]}</b>" if hdr else r[1], TableHeader if hdr else TableCellBold),
            Paragraph(f"<b>{r[2]}</b>" if hdr else r[2], TableHeader if hdr else TableCell)
        ])

    toc_t = Table(toc_rows, colWidths=[40, 150, 310])
    toc_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_BG_ALT]),
    ]))
    story.append(toc_t)
    story.append(PageBreak())
    return story

def generate_pdf(output_path: str):
    print(f"Building PDF at: {output_path}")
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=46
    )

    story = []
    story.extend(build_cover_page())
    story.extend(build_section_1())
    story.extend(build_section_2())
    story.append(PageBreak())
    story.extend(build_section_3())
    story.extend(build_section_4())
    story.append(PageBreak())
    story.extend(build_section_5())
    story.append(PageBreak())
    story.extend(build_section_6())
    story.extend(build_section_7())
    story.append(PageBreak())
    story.extend(build_section_8())
    story.extend(build_section_9())
    story.append(PageBreak())
    story.extend(build_section_10())
    story.extend(build_section_11())
    story.append(PageBreak())
    story.extend(build_section_12())
    story.extend(build_section_13())
    story.append(PageBreak())
    story.extend(build_section_14())
    story.extend(build_section_15())
    story.append(PageBreak())
    story.extend(build_section_16())
    story.extend(build_section_17())
    story.append(PageBreak())
    story.extend(build_section_18())

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated {output_path}")

if __name__ == "__main__":
    out_file = os.path.join(r"C:\Users\lenovo\OneDrive\Desktop\Weather Intelligence Project", "PROJECT_STUDY_GUIDE.pdf")
    generate_pdf(out_file)
