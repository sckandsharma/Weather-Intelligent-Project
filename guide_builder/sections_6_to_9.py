"""
Sections 6 to 9 of the Study Guide:
6. Database Architecture, ER Diagram & pgvector
7. Authentication & Security Architecture
8. Weather API Integration & Caching Layer
9. RAG Pipeline, Ingestion & Semantic Retrieval
"""
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
from reportlab.lib import colors
from guide_builder.styles import (
    H1, H2, H3, Body, BodyBold, BodySmall, BulletText, TableHeader, TableCell, TableCellBold, TableCellCode,
    PRIMARY, PRIMARY_LIGHT, ACCENT, ROW_BG_ALT, BORDER_COLOR, make_callout, make_code_box
)

def build_section_6():
    story = []
    story.append(Paragraph("6. Database Architecture, ER Diagram & pgvector", H1))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph(
        "The project uses <b>PostgreSQL 16</b> with the <b>pgvector</b> extension enabled. The schema is organized into "
        "nine normalized tables that handle user authentication, multi-turn chat sessions, vector embeddings, external API auditing, "
        "and evaluation records.",
        Body
    ))

    # ER Diagram
    er_diagram = (
        "                    +-----------------------+\n"
        "                    |         users         |\n"
        "                    +-----------------------+\n"
        "                    | PK id                 |\n"
        "                    |    email (UNIQUE)     |\n"
        "                    |    password_hash      |\n"
        "                    |    role (ENUM)        |\n"
        "                    +-----------------------+\n"
        "                        | 1              | 1\n"
        "                        |                | \n"
        "                        | N              | N\n"
        "                        v                v\n"
        "+-----------------------+     +-----------------------+\n"
        "|     conversations     |     |      audit_logs       |\n"
        "+-----------------------+     +-----------------------+\n"
        "| PK id                 |     | PK id                 |\n"
        "| FK user_id (CASCADE)  |     | FK user_id (SET NULL) |\n"
        "|    title              |     |    action             |\n"
        "|    created_at         |     |    resource           |\n"
        "+-----------------------+     +-----------------------+\n"
        "           | 1\n"
        "           | N\n"
        "           v\n"
        "+-----------------------+     +-----------------------+     +-----------------------+\n"
        "|       messages        |     |       documents       |     |   weather_api_logs    |\n"
        "+-----------------------+     +-----------------------+     +-----------------------+\n"
        "| PK id                 |     | PK id                 |     | PK id                 |\n"
        "| FK conv_id (CASCADE)  |     |    title              |     |    city               |\n"
        "|    question           |     |    source_url         |     |    request_params (JSONB)\n"
        "|    answer             |     |    category           |     |    response_json (JSONB)\n"
        "|    created_at         |     |    version            |     |    latency_ms         |\n"
        "+-----------------------+     +-----------------------+     +-----------------------+\n"
        "           | 1                            | 1\n"
        "           | N                            | N\n"
        "           v                              v\n"
        "+-----------------------+     +-----------------------+     +-----------------------+\n"
        "|       feedback        |     |    document_chunks    |     |  evaluation_results   |\n"
        "+-----------------------+     +-----------------------+     +-----------------------+\n"
        "| PK id                 |     | PK id                 |     | PK id                 |\n"
        "| FK message_id(CASCADE)|     | FK document_id(CASCAD)|     |    run_id             |\n"
        "|    rating (1-5)       |     |    chunk_text         |     |    test_case_id       |\n"
        "|    comments           |     |    embedding Vector(384)    |    routing_score      |\n"
        "+-----------------------+     |    metadata (JSONB)   |     |    retrieval_score    |\n"
        "                              +-----------------------+     |    answer_score       |\n"
        "                                                            +-----------------------+"
    )
    story.append(make_code_box(er_diagram))
    story.append(Spacer(1, 8))

    story.append(Paragraph("6.1 All 9 Database Tables: Purpose, Columns & Code Access", H2))

    tables_spec = [
        ["users", "Stores registered user accounts, bcrypt/Argon2 hashes, and RBAC roles.",
         "id (PK, int), full_name (str), email (str, UNIQUE, index), password_hash (str), role (UserRole enum: ADMIN/USER/EVALUATOR), is_active (bool), created_at, updated_at",
         "Written by: app/api/auth.py (register)<br/>Read by: app/auth/dependencies.py (get_current_user), app/api/auth.py (login)"],
        ["conversations", "Tracks chat sessions owned by users. Enforces per-user privacy.",
         "id (PK, int), user_id (FK -> users.id, ON DELETE CASCADE, index), title (str), created_at (timestamp)",
         "Written by: app/services/chat_service.py (_get_or_create_conversation)<br/>Read by: app/api/chat.py (get_chat_history)"],
        ["messages", "Stores individual conversation turns (question, answer, timestamps).",
         "id (PK, int), conversation_id (FK -> conversations.id, ON DELETE CASCADE, index), question (text), answer (text), created_at (timestamp)",
         "Written by: app/services/chat_service.py (_save_message_and_respond)<br/>Read by: app/api/chat.py (history), services/chat_service.py"],
        ["documents", "Master catalog of ingested PDF guidelines (NDMA, IMD, NOAA).",
         "id (PK, int), title (str), source_url (str), category (str, index), version (str, default '1.0'), created_at (timestamp)",
         "Written by: app/rag/ingestion.py (ingest_text)<br/>Read by: app/api/documents.py (list_documents)"],
        ["document_chunks", "RAG vector store holding text segments and 384-dimensional dense vectors.",
         "id (PK, int), document_id (FK -> documents.id, ON DELETE CASCADE, index), chunk_text (text), embedding (Vector(384)), metadata (JSONB, default {})",
         "Written by: app/rag/ingestion.py (ingest_text)<br/>Read by: app/rag/retrieval.py (retrieve_relevant_chunks via cosine search)"],
        ["weather_api_logs", "Persistent audit log of every call made to Open-Meteo.",
         "id (PK, int), city (str, index), request_params (JSONB), response_json (JSONB, nullable), status_code (int), latency_ms (float), created_at (timestamp, index)",
         "Written by: app/services/logging_service.py (log_weather_api_call)<br/>Read by: system administrators and test assertions"],
        ["feedback", "End-user satisfaction ratings (1 to 5 stars) on assistant answers.",
         "id (PK, int), message_id (FK -> messages.id, ON DELETE CASCADE, index), rating (int, 1-5), comments (text, nullable)",
         "Written by: app/api/chat.py (submit_feedback)<br/>Read by: quality assurance analysis"],
        ["evaluation_results", "Automated benchmark scoring runs against the 15 official test cases.",
         "id (PK, int), run_id (str, nullable, index), test_case_id (str, index), routing_score (float), retrieval_score (float, nullable), answer_score (float), latency_ms (float), created_at (timestamp, index)",
         "Written by: app/evaluation/evaluator.py (run_evaluation_benchmark)<br/>Read by: app/api/evaluation.py (get_evaluation_results), Streamlit Tab 3"],
        ["audit_logs", "Security compliance event trail (logins, evaluations, chat events).",
         "id (PK, int), user_id (FK -> users.id, ON DELETE SET NULL, nullable, index), action (str, index), resource (str), timestamp (timestamp, index)",
         "Written by: app/services/logging_service.py (log_audit_event)<br/>Read by: security audit inspection"]
    ]

    table_rows = [[
        Paragraph("<b>Table Name</b>", TableHeader),
        Paragraph("<b>Purpose & Role</b>", TableHeader),
        Paragraph("<b>Columns & Constraints</b>", TableHeader),
        Paragraph("<b>Accessing Code Files</b>", TableHeader)
    ]]
    for t in tables_spec:
        table_rows.append([
            Paragraph(t[0], TableCellBold),
            Paragraph(t[1], TableCell),
            Paragraph(t[2], TableCellCode),
            Paragraph(t[3], TableCell)
        ])

    t = Table(table_rows, colWidths=[65, 120, 185, 150])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_BG_ALT]),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    story.append(Paragraph("6.2 Deep Dive: pgvector & Database Migrations", H2))
    pgvector_desc = (
        "<b>pgvector Implementation Details:</b><br/>"
        "• <b>Vector Dimension:</b> Exactly 384 dimensions, matching the output of the <code>all-MiniLM-L6-v2</code> SentenceTransformer model.<br/>"
        "• <b>Distance Operator:</b> Cosine distance is used via the <code>&lt;=&gt;</code> operator. The SQL expression is:<br/>"
        "&nbsp;&nbsp;<code>DocumentChunk.embedding.cosine_distance(query_vector)</code><br/>"
        "• <b>Similarity Score Calculation:</b> Converted to a 0.0 to 1.0 similarity score using:<br/>"
        "&nbsp;&nbsp;<code>similarity = 1.0 - distance</code> (clamped to [0.0, 1.0]).<br/>"
        "• <b>JSONB Columns:</b> Used in <code>weather_api_logs</code> (request_params, response_json) and <code>document_chunks</code> (metadata). "
        "PostgreSQL JSONB provides binary-parsed JSON storage with indexing capability and schema flexibility without requiring separate table columns for dynamic metadata.<br/>"
        "• <b>Alembic Migrations:</b> Three sequential migrations exist:<br/>"
        "&nbsp;&nbsp;1. <code>bf35a3341da8</code>: Creates initial <code>users</code> table.<br/>"
        "&nbsp;&nbsp;2. <code>39fe8ebd5e3a</code>: Executes <code>CREATE EXTENSION IF NOT EXISTS vector</code> and creates the remaining 8 tables.<br/>"
        "&nbsp;&nbsp;3. <code>662e79249848</code>: Adds <code>run_id</code> and makes <code>retrieval_score</code> nullable in <code>evaluation_results</code>."
    )
    story.append(Paragraph(pgvector_desc, Body))
    story.append(Spacer(1, 10))
    return story

def build_section_7():
    story = []
    story.append(Paragraph("7. Authentication & Security Architecture", H1))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))
    
    auth_desc = (
        "Security is implemented following the principle of defense-in-depth across five complementary layers: "
        "cryptographic password hashing, dual-token JWT lifecycle, token revocation, role-based access control, "
        "and IP-based rate limiting.<br/><br/>"
        "<b>1. Dual-Token JWT Lifecycle:</b><br/>"
        "• <b>Access Token:</b> Short-lived (30 minutes). Signed with <code>JWT_SECRET_KEY</code> using HMAC-SHA256 (<code>HS256</code>). "
        "Payload includes <code>sub</code> (user ID), <code>role</code>, <code>type='access'</code>, and <code>exp</code>. Required on every protected endpoint.<br/>"
        "• <b>Refresh Token:</b> Long-lived (7 days). Payload contains <code>sub</code> and <code>type='refresh'</code>. Exchanged via <code>POST /auth/refresh</code> "
        "to obtain a fresh access token without re-entering credentials.<br/>"
        "• <b>Token Invalidation on Logout:</b> When a user calls <code>POST /auth/logout</code>, the active access token is placed into an in-memory "
        "revocation blacklist (<code>_revoked_tokens</code> in <code>app/core/security.py</code>). Future requests presenting this token are rejected with 401 Unauthorized.<br/><br/>"
        "<b>2. Role-Based Access Control (RBAC):</b><br/>"
        "The system defines three roles in <code>UserRole</code> enum: <code>USER</code>, <code>ADMIN</code>, and <code>EVALUATOR</code>.<br/>"
        "• <code>USER</code>: Can access chat, weather, own conversation history, and submit feedback.<br/>"
        "• <code>EVALUATOR</code>: Can trigger automated benchmark evaluation (<code>POST /evaluation/run</code>) and view benchmark result history.<br/>"
        "• <code>ADMIN</code>: Can view all system users (<code>GET /users/</code>) and promote/demote roles (<code>PATCH /users/{id}/role</code>).<br/>"
        "Enforced declaratively via <code>Depends(require_admin)</code> and <code>Depends(require_evaluator)</code> in route signatures.<br/><br/>"
        "<b>3. Rate Limiting via SlowAPI:</b><br/>"
        "To protect against brute-force credential stuffing and denial-of-service, SlowAPI enforces limits keyed by remote client IP address:<br/>"
        "• <code>POST /auth/register</code> and <code>POST /auth/login</code>: <b>5 requests / minute</b>.<br/>"
        "• <code>POST /chat/ask</code>: <b>30 requests / minute</b>.<br/>"
        "Excess requests receive an immediate <code>HTTP 429 Too Many Requests</code> with a standard <code>Retry-After</code> header.<br/><br/>"
        "<b>4. Per-User Data Isolation:</b><br/>"
        "Conversations and messages are strictly scoped to the authenticated user ID. In <code>app/api/chat.py</code>, if User A attempts to view "
        "User B's conversation ID, the query returns <code>HTTP 404 Not Found</code> (rather than 403 Forbidden). Returning 404 prevents malicious "
        "actors from enumerating whether specific conversation IDs exist in the system."
    )
    story.append(Paragraph(auth_desc, Body))
    story.append(Spacer(1, 10))
    return story

def build_section_8():
    story = []
    story.append(Paragraph("8. Weather API Integration & Caching Layer", H1))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))
    
    weather_desc = (
        "The weather subsystem delivers real-time weather observations and multi-day forecasts through Open-Meteo, "
        "an open-access meteorological API that requires no API key, backed by a resilient Redis caching layer.<br/><br/>"
        "<b>1. City Geocoding with Indian Alias Normalization:</b><br/>"
        "Before calling weather forecast APIs, city names are resolved to latitude/longitude coordinates via Open-Meteo's geocoding service. "
        "To eliminate user failures from common colloquial or historical Indian city spellings, <code>app/weather/geocoding.py</code> maintains "
        "a canonical alias dictionary:<br/>"
        "• <code>badmer</code> $\\rightarrow$ <code>Barmer</code> (fixes Open-Meteo 404 on Badmer)<br/>"
        "• <code>bombay</code> $\\rightarrow$ <code>Mumbai</code>, <code>calcutta</code> $\\rightarrow$ <code>Kolkata</code>, <code>madras</code> $\\rightarrow$ <code>Chennai</code><br/>"
        "• <code>bengaluru</code> $\\rightarrow$ <code>Bangalore</code>, <code>prayagraj</code> $\\rightarrow$ <code>Allahabad</code>, <code>banaras</code> $\\rightarrow$ <code>Varanasi</code><br/><br/>"
        "<b>2. Supported Query Modes & Date Validation:</b><br/>"
        "• <b>Current Weather:</b> Returns temperature (°C), relative humidity (%), wind speed (km/h), precipitation (mm), UV index, and WMO condition string.<br/>"
        "• <b>Daily Forecast:</b> Validates days between 1 and 16 (<code>validate_forecast_days</code>). Raises <code>InvalidDateRangeError</code> (HTTP 400) if >16.<br/>"
        "• <b>Hourly Forecast:</b> Validates hours between 1 and 168 (7 days) (<code>validate_hourly_hours</code>).<br/>"
        "• <b>Target Date Validation:</b> <code>validate_target_date</code> parses relative strings ('today', 'tomorrow', 'overmorrow') and ISO dates, "
        "rejecting dates in the past or beyond the 16-day meteorological window.<br/><br/>"
        "<b>3. Redis Caching & Visual Cache Flags:</b><br/>"
        "Every weather response is cached in Redis (database 0) with a <b>600-second (10-minute) TTL</b>:<br/>"
        "• Cache Keys: <code>weather:current:&lt;city&gt;</code>, <code>weather:daily:&lt;city&gt;:&lt;days&gt;</code>, <code>weather:hourly:&lt;city&gt;:&lt;hours&gt;</code><br/>"
        "• <b>First Request (Cache Miss):</b> API fetches from Open-Meteo (~650ms), writes to Redis, returns JSON with <code>\"cached\": false</code>.<br/>"
        "• <b>Subsequent Requests (Cache Hit):</b> API returns cached dictionary from Redis memory in under 5ms with <code>\"cached\": true</code>.<br/>"
        "• <b>In-Memory Fallback:</b> If Redis is unreachable, <code>CacheService</code> stores keys in a local Python dictionary with timestamp expiry, "
        "guaranteeing zero 500 errors during Redis maintenance.<br/><br/>"
        "<b>4. Complete API Call Auditing:</b><br/>"
        "Every external call to Open-Meteo is persisted in the <code>weather_api_logs</code> table with city name, request parameters, response JSON, "
        "HTTP status code, and latency in milliseconds. This provides full traceability for rate-limit monitoring and billing verification."
    )
    story.append(Paragraph(weather_desc, Body))
    story.append(Spacer(1, 10))
    return story

def build_section_9():
    story = []
    story.append(Paragraph("9. RAG Pipeline, Ingestion & Semantic Retrieval", H1))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))
    
    rag_desc = (
        "The Retrieval-Augmented Generation (RAG) system provides authoritative disaster preparedness guidelines and meteorological definitions "
        "grounded in verified government and scientific documentation.<br/><br/>"
        "<b>1. Official Document Corpus (7 Pre-Ingested Guidelines):</b><br/>"
        "1. <code>ndma_heatwave_guidelines.pdf</code> (NDMA) — Hydration, ORS, vulnerable groups, dos and don'ts.<br/>"
        "2. <code>imd_color_coded_weather_warnings.pdf</code> (IMD) — Green (no warning), Yellow (be updated), Orange (be prepared), Red (take action).<br/>"
        "3. <code>ndma_cyclone_safety_guidelines.pdf</code> (NDMA) — Structural safety, coastal evacuation, storm surge protocols.<br/>"
        "4. <code>noaa_cyclone_vs_hurricane_terminology.pdf</code> (NOAA) — Regional terminology (typhoons in NW Pacific, hurricanes in Atlantic, cyclones in Indian Ocean).<br/>"
        "5. <code>mountain_hiking_weather_safety.pdf</code> — Hypothermia, lightning safety, 30-30 rule, flash floods in high altitudes.<br/>"
        "6. <code>rain_thunderstorm_and_flood_safety.pdf</code> — Electrical safety, moving water driving hazards, shelter protocols.<br/>"
        "7. <code>ndma_cold_wave_safety_guidelines.pdf</code> (NDMA) — Frostbite, multi-layered clothing, home heating ventilation.<br/><br/>"
        "<b>2. Text Cleaning & Chunking Strategy:</b><br/>"
        "• <b>Chunk Size:</b> <b>500 characters</b> with <b>50 characters overlap</b>.<br/>"
        "• <i>Why 500 characters?</i> 500 characters equates to approximately 80–100 words. This provides concise, single-topic paragraphs "
        "that comfortably fit within the 256-word token limit of <code>all-MiniLM-L6-v2</code> without truncation, maximizing embedding precision.<br/>"
        "• <i>Why 50 character overlap?</i> Preserves semantic continuity across split boundaries, ensuring that sentences split near the edge "
        "do not lose their subject or meaning.<br/>"
        "• <b>Smart Boundary Detection:</b> <code>split_text_into_chunks</code> searches backward for paragraph breaks (<code>\\n\\n</code>) and sentence "
        "terminators (<code>. </code>, <code>? </code>, <code>! </code>) past the halfway mark of each window rather than cutting words in half.<br/><br/>"
        "<b>3. Embedding Model Selection (all-MiniLM-L6-v2):</b><br/>"
        "• Produces <b>384-dimensional dense vector embeddings</b>.<br/>"
        "• Loaded locally via HuggingFace SentenceTransformers and cached as an LRU singleton (<code>maxsize=1</code>).<br/>"
        "• Pre-downloaded into the Docker image at build time (<code>/home/appuser/.cache/huggingface</code>) to eliminate runtime internet dependencies.<br/>"
        "• Chosen over OpenAI embeddings because it runs 100% locally on CPU in ~15ms, costs $0, and ensures user queries never leave the system for vectorization.<br/><br/>"
        "<b>4. Cosine Similarity Retrieval & Threshold Filtering:</b><br/>"
        "• When a query is received, it is embedded into a 384-dim vector and compared against all rows in <code>document_chunks</code> using PostgreSQL pgvector.<br/>"
        "• <b>Similarity Threshold:</b> <b>0.30</b> (maximum cosine distance of $1.0 - 0.30 = 0.70$). Any chunks with similarity below 0.30 are discarded as irrelevant noise.<br/>"
        "• <b>Top-K Limit:</b> At most <b>5 chunks</b> are returned to prevent LLM context saturation.<br/>"
        "• <b>Citation Provenance:</b> Every retrieved chunk is mapped to a <code>DocumentSource</code> containing document title, category, chunk index, "
        "and source URL, ensuring full transparency in generated answers."
    )
    story.append(Paragraph(rag_desc, Body))
    story.append(Spacer(1, 10))
    return story
