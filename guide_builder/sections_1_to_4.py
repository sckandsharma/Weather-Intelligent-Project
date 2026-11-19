"""
Sections 1 to 4 of the Study Guide:
1. Project Overview
2. File Classification Table
3. Architecture & Connectivity
4. Complete Request Flows
"""
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
from reportlab.lib import colors
from guide_builder.styles import (
    H1, H2, H3, Body, BodyBold, BodySmall, BulletText, TableHeader, TableCell, TableCellBold, TableCellCode,
    PRIMARY, PRIMARY_LIGHT, ACCENT, ROW_BG_ALT, BORDER_COLOR, make_callout, make_code_box
)

def build_section_1():
    story = []
    story.append(Paragraph("1. Project Overview", H1))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))
    
    overview_text = (
        "<b>What it does:</b> An enterprise-grade, conversational Weather Intelligence and Disaster Advisory Assistant "
        "that combines real-time meteorological data with an official disaster preparedness knowledge base. "
        "It dynamically determines user intent and answers questions about current weather, multi-day forecasts, "
        "and disaster safety guidelines without hallucinating numbers.<br/>"
        "<b>Who uses it:</b> Daily commuters checking rain/heat, outdoor planners (trekkers, hikers, event managers), "
        "vulnerable populations (elderly during heatwaves), and civil emergency personnel.<br/>"
        "<b>Example questions handled:</b><br/>"
        "• <i>'What is the temperature in Delhi right now?'</i> (Live weather observation)<br/>"
        "• <i>'What precautions should be taken during a severe heatwave?'</i> (RAG knowledge base)<br/>"
        "• <i>'Is hiking in Manali safe tomorrow?'</i> (Hybrid: Live forecast + mountain safety advisory)<br/>"
        "• <i>'Jaipur me barish ha kya?'</i> (Multilingual colloquial Hinglish weather query)<br/>"
        "• <i>'What is Apple's latest stock price?'</i> (Guardrail: polite out-of-scope refusal)"
    )
    story.append(Paragraph(overview_text, Body))
    story.append(Spacer(1, 6))

    analogy = (
        "<b>Plain-English Analogy:</b> Think of this system as an expert airport flight operations desk. "
        "When you ask a question, the front officer (FastAPI + JWT) checks your passport. "
        "The smart traffic dispatcher (Router) decides what you need: looking out the window at the live radar "
        "(Open-Meteo Weather API + Redis cache), consulting the official civil aviation safety manual (RAG + pgvector), "
        "or combining both. Finally, the chief briefing officer (Gemini LLM) reads the verified numbers and regulations "
        "to formulate a grounded, safety-compliant briefing with source citations."
    )
    story.append(make_callout("The Layman's Mental Model", analogy, "info"))
    story.append(Spacer(1, 10))
    return story

def build_section_2():
    story = []
    story.append(Paragraph("2. Complete File Classification", H1))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))
    story.append(Paragraph(
        "Every file in the repository categorized by architectural role, with its exact location and responsibility:",
        Body
    ))

    files_data = [
        # FastAPI Gateway & App
        ["FastAPI Core", "app/main.py", "FastAPI app instance, CORS middleware, SlowAPI rate-limiting handler, health checks."],
        ["FastAPI Core", "entrypoint.sh", "Container boot script: executes Alembic migrations then launches Uvicorn."],
        # Configuration & Settings
        ["Config", "app/core/config.py", "Pydantic Settings reading .env (DB URL, Redis, JWT secrets, Gemini model)."],
        ["Config", ".env / .env.example", "Environment variable definitions for local and Dockerized runtime environments."],
        ["Config", "alembic.ini", "Alembic configuration file specifying migration script location and logging."],
        ["Config", "requirements.txt", "Pinned Python dependencies (FastAPI, SQLAlchemy, psycopg, pgvector, google-genai)."],
        # Authentication & Security
        ["Auth / Security", "app/auth/jwt_handler.py", "Encodes and decodes HMAC-SHA256 JWT access (30m) and refresh (7d) tokens."],
        ["Auth / Security", "app/auth/password.py", "Argon2id password hashing and constant-time verification using pwdlib."],
        ["Auth / Security", "app/auth/dependencies.py", "FastAPI Depends: get_current_user, require_admin, require_evaluator."],
        ["Auth / Security", "app/core/security.py", "SlowAPI rate limiter instance and in-memory revoked JWT token set."],
        ["Auth / Security", "app/api/auth.py", "REST endpoints for register (201), login (tokens), refresh, logout, profile."],
        ["Auth / Security", "app/api/users.py", "REST endpoints for user profile, admin user listing, and role updates."],
        ["Auth / Security", "app/schemas/auth.py", "Pydantic models for LoginRequest, TokenPair, RefreshTokenRequest."],
        ["Auth / Security", "app/schemas/user.py", "Pydantic models for UserCreate (validation) and UserResponse (ORM mode)."],
        # Database & ORM
        ["Database", "app/database/session.py", "SQLAlchemy engine with pool_pre_ping=True, SessionLocal factory, get_db dependency."],
        ["Database", "app/database/models.py", "SQLAlchemy ORM models for all 9 tables (User, Conversation, Message, etc.)."],
        ["Database", "alembic/env.py", "Alembic runtime harness reading Base.metadata for offline/online migrations."],
        ["Database", "alembic/versions/*.py", "Database migration scripts (users table, remaining 8 tables + pgvector, run_id)."],
        # Weather Integration
        ["Weather", "app/weather/geocoding.py", "Open-Meteo geocoding client with Indian city alias mapping (Badmer -> Barmer)."],
        ["Weather", "app/weather/client.py", "Low-level HTTP client calling Open-Meteo forecast API with latency tracking."],
        ["Weather", "app/weather/service.py", "High-level weather orchestrator: current, 1-16d daily, 1-168h hourly, cache, logs."],
        ["Weather", "app/api/weather.py", "JWT-protected REST endpoints: GET /current, GET /forecast, GET /hourly."],
        # Caching & Logging
        ["Caching", "app/services/cache_service.py", "Redis cache wrapper with automatic in-memory dict fallback and TTL management."],
        ["Logging", "app/services/logging_service.py", "Database persistence helpers for weather API logs and security audit logs."],
        # RAG Knowledge Base
        ["RAG", "app/rag/chunking.py", "Text cleaning and character chunking (500 chars, 50 overlap) with sentence boundaries."],
        ["RAG", "app/rag/embeddings.py", "Loads all-MiniLM-L6-v2 (LRU cached) to generate 384-dimensional normalized vectors."],
        ["RAG", "app/rag/ingestion.py", "Parsers for PDF, HTML, DOCX, TXT, MD; deduplication and vector DB storage."],
        ["RAG", "app/rag/retrieval.py", "Cosine distance vector search (<=>) with 0.30 similarity threshold and top-k."],
        ["RAG", "app/api/documents.py", "REST endpoints to list ingested knowledge base documents and chunk stats."],
        ["RAG", "scripts/ingest_documents.py", "CLI utility script to bulk-ingest 7 official NDMA/IMD disaster safety PDFs."],
        # AI / LLM & Routing
        ["AI / LLM", "app/llm/router.py", "Deterministic regex intent router (weather, rag, both, neither, clarification)."],
        ["AI / LLM", "app/llm/prompts.py", "XML prompt builder, official alert directive, system instructions, confidence."],
        ["AI / LLM", "app/llm/generator.py", "Gemini 3.5 Flash Lite client using google-genai SDK, retry logic, error mapping."],
        ["AI / LLM", "app/services/chat_service.py", "Full pipeline orchestrator: history recovery, weather, RAG, prompt, DB save."],
        ["AI / LLM", "app/api/chat.py", "Rate-limited (30/min) chat endpoints: POST /chat/ask, GET /history, POST /feedback."],
        ["AI / LLM", "app/schemas/chat.py", "Pydantic models for ChatRequest, ChatResponse, Feedback, Conversation."],
        # Evaluation & Benchmarking
        ["Evaluation", "app/evaluation/dataset.json", "Official 15 test cases with ground truth routing, categories, and keywords."],
        ["Evaluation", "app/evaluation/metrics.py", "Deterministic scoring functions: routing score, retrieval score, answer score."],
        ["Evaluation", "app/evaluation/evaluator.py", "End-to-end benchmark runner, DB persistence, and markdown report generator."],
        ["Evaluation", "app/api/evaluation.py", "Evaluator-role REST endpoints: POST /evaluation/run, GET /evaluation/results."],
        ["Evaluation", "evaluation_report.md", "Official 15/15 passed benchmark report with latency percentiles."],
        # Frontend UI
        ["Frontend", "frontend/streamlit_app.py", "Streamlit 4-tab UI: Chat, Live Explorer, Benchmark Dashboard, Knowledge Docs."],
        ["Frontend", "frontend/app.py", "Entrypoint wrapper module re-exporting streamlit_app."],
        # Pytest Test Suite
        ["Tests", "tests/conftest.py", "Pytest fixtures: rollback DB transactions, TestClient, user tokens, rate limiter bypass."],
        ["Tests", "tests/test_api.py", "Smoke tests for root / and health endpoints /health, /health/database."],
        ["Tests", "tests/test_auth.py", "Tests for register, login, refresh, logout, token revocation, RBAC, 429 limiter."],
        ["Tests", "tests/test_chat.py", "Tests for /chat/ask: out-of-scope refusal, clarification, weather failure, end-to-end."],
        ["Tests", "tests/test_database.py", "Tests for conversation isolation, message pagination, and pgvector cosine search."],
        ["Tests", "tests/test_evaluation.py", "Unit tests for scoring metrics and evaluator role access restrictions."],
        ["Tests", "tests/test_rag.py", "Tests for text cleaning, chunking boundaries, doc ingestion, and similarity retrieval."],
        ["Tests", "tests/test_router.py", "Tests for word boundaries (training!=rain), missing location, 15 benchmark questions."],
        ["Tests", "tests/test_weather.py", "Tests for geocoding, Open-Meteo client, cache hit/miss, and date validation."],
        # Docker Infrastructure
        ["Docker / DevOps", "Dockerfile", "Multi-stage hardened build (builder + runner), non-root appuser, pre-cached embeddings."],
        ["Docker / DevOps", "docker-compose.yml", "Orchestrates 4 services: db (pgvector), redis, api (FastAPI), frontend (Streamlit)."],
        ["Docker / DevOps", ".dockerignore", "Excludes venv, .git, __pycache__, and .env secrets from Docker build context."],
        ["Documentation", "README.md", "Complete architectural documentation, trade-off matrix, Mermaid diagrams, API table."],
    ]

    table_rows = [[
        Paragraph("<b>Category</b>", TableHeader),
        Paragraph("<b>File Path</b>", TableHeader),
        Paragraph("<b>Primary Architectural Responsibility</b>", TableHeader)
    ]]
    for r in files_data:
        table_rows.append([
            Paragraph(r[0], TableCellBold),
            Paragraph(r[1], TableCellCode),
            Paragraph(r[2], TableCell)
        ])

    t = Table(table_rows, colWidths=[80, 140, 300])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_BG_ALT]),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))
    return story

def build_section_3():
    story = []
    story.append(Paragraph("3. System Architecture & Component Connectivity", H1))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph(
        "The system is structured as a decoupled, microservice-style architecture where every component has a strict, "
        "single responsibility. The diagram below illustrates how user traffic flows from the presentation layer "
        "to backend services and external APIs:",
        Body
    ))

    arch_diagram = (
        "+---------------------------------------------------------------------------------------------------+\n"
        "|                                     PRESENTATION TIER                                            |\n"
        "|  Streamlit UI (:8501)  <--->  FastAPI Swagger UI (:8000/docs)  <--->  Third-party REST Clients   |\n"
        "+---------------------------------------------------------------------------------------------------+\n"
        "                                                 |  HTTP + Bearer JWT Token\n"
        "                                                 v\n"
        "+---------------------------------------------------------------------------------------------------+\n"
        "|                                      FASTAPI API GATEWAY                                          |\n"
        "|  CORSMiddleware  -->  SlowAPI RateLimiter (IP/Endpoint)  -->  HTTPBearer & JWT Auth Guard         |\n"
        "+---------------------------------------------------------------------------------------------------+\n"
        "                                                 |\n"
        "                                                 v\n"
        "+---------------------------------------------------------------------------------------------------+\n"
        "|                                    DETERMINISTIC INTENT ROUTER                                     |\n"
        "|  Classifies into:  [WEATHER]    |    [RAG]    |    [BOTH]    |    [CLARIFICATION]    |    [NEITHER] |\n"
        "+---------------------------------------------------------------------------------------------------+\n"
        "             |                               |                            |                     |\n"
        "             v                               v                            v                     v\n"
        "+--------------------------+    +--------------------------+    +-------------------+  +------------+\n"
        "|   WEATHER ORCHESTRATOR   |    |      RAG RETRIEVER       |    | CLARIFICATION     |  | OUT-OF-    |\n"
        "|  1. Geocode (Aliasing)   |    |  1. Query Embedding      |    | Prompts user for  |  | SCOPE      |\n"
        "|  2. Check Redis Cache    |    |     (all-MiniLM-L6-v2)   |    | missing city/time |  | Polite     |\n"
        "|  3. Call Open-Meteo API  |    |  2. Cosine Distance Search|   +-------------------+  | Refusal    |\n"
        "|  4. Log API Call to DB   |    |     pgvector (threshold  |                          +------------+\n"
        "|  5. Store Cache (600s)   |    |     >= 0.30, top-k=5)    |                                        |\n"
        "+--------------------------+    +--------------------------+                                        |\n"
        "             |                               |                                                      |\n"
        "             +-------------------------------+------------------------------------------------------+\n"
        "                                             |\n"
        "                                             v\n"
        "+---------------------------------------------------------------------------------------------------+\n"
        "|                                   XML PROMPT ASSEMBLER                                            |\n"
        "|  System Instruction + <live_weather> + <knowledge_context> + <conversation_history> + Guidelines   |\n"
        "+---------------------------------------------------------------------------------------------------+\n"
        "                                             |\n"
        "                                             v\n"
        "+---------------------------------------------------------------------------------------------------+\n"
        "|                            GOOGLE GEMINI 3.5 FLASH LITE ENGINE                                    |\n"
        "|  Temperature 0.2 (deterministic) | Anti-hallucination Grounding | Source Citations                 |\n"
        "+---------------------------------------------------------------------------------------------------+\n"
        "                                             |\n"
        "                                             v\n"
        "+---------------------------------------------------------------------------------------------------+\n"
        "|                         PERSISTENCE & AUDIT TIER (PostgreSQL + Redis)                             |\n"
        "|  users | conversations | messages | feedback | weather_api_logs | audit_logs | evaluation_results |\n"
        "+---------------------------------------------------------------------------------------------------+"
    )
    story.append(make_code_box(arch_diagram))
    story.append(Spacer(1, 8))

    connectivity_desc = (
        "<b>Component Interconnections:</b><br/>"
        "1. <b>Client to API Gateway:</b> Streamlit communicates with FastAPI via standard HTTP/JSON requests over Docker network bridge "
        "(<code>http://api:8000/api/v1</code>). All requests carry an <code>Authorization: Bearer &lt;token&gt;</code> header.<br/>"
        "2. <b>API Gateway to Security:</b> Before hitting any endpoint handler, SlowAPI verifies that the client has not exceeded "
        "rate limits (5 requests/min on auth, 30 requests/min on chat). The dependency <code>get_current_user</code> verifies the JWT "
        "signature against <code>JWT_SECRET_KEY</code>, checks expiration, and ensures the token has not been revoked in the in-memory blacklist.<br/>"
        "3. <b>Service to Redis Cache:</b> The weather service queries Redis (port 6379) using key format <code>weather:current:&lt;city&gt;</code>. "
        "If a cache hit occurs, Open-Meteo is never contacted. If Redis fails or is unavailable, the <code>CacheService</code> seamlessly falls "
        "back to an internal memory dictionary without throwing an error.<br/>"
        "4. <b>Service to PostgreSQL / pgvector:</b> SQLAlchemy connects to Postgres via psycopg3 driver (port 5432 inside Docker, 5433 host). "
        "Vector search uses pgvector's cosine distance operator (<code>&lt;=&gt;</code>) executed natively in the database engine.<br/>"
        "5. <b>Service to Google Gemini:</b> LLM calls use the modern <code>google-genai</code> SDK, invoking <code>gemini-3.5-flash-lite</code> "
        "via Starlette's <code>run_in_threadpool</code> to bypass Windows async SSL event loop blocking."
    )
    story.append(Paragraph(connectivity_desc, Body))
    story.append(Spacer(1, 10))
    return story

def build_section_4():
    story = []
    story.append(Paragraph("4. Complete Step-by-Step Request Flows", H1))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph("4.1 Deep Dive Flow: <i>'Is hiking in Manali safe tomorrow?'</i> (Hybrid Query)", H2))
    story.append(Paragraph(
        "This is the most complex path in the system because it engages every single layer: authentication, intent routing, "
        "location extraction, date parsing, live weather API calling, vector search retrieval, prompt assembly, LLM synthesis, "
        "database persistence, and audit logging. Here is the exact path down to the function and file level:",
        Body
    ))

    deep_steps = [
        ["1. UI Submission", "frontend/streamlit_app.py", "User types query into st.chat_input(). Sends POST request to /api/v1/chat/ask with payload: {'message': 'Is hiking in Manali safe tomorrow?', 'conversation_id': None} and auth headers."],
        ["2. Rate Limiting", "app/core/security.py", "SlowAPI @limiter.limit('30/minute') checks client IP address. Request is within threshold; execution continues."],
        ["3. Authentication", "app/auth/dependencies.py", "get_current_user() intercepts request. Reads Bearer token, calls jwt_handler.decode_token(), checks is_token_revoked(), loads User from PostgreSQL, verifies is_active=True."],
        ["4. Chat Handler", "app/api/chat.py", "ask_chat() receives ChatRequest, current_user, and db session. Forwards to chat_service.process_chat_message()."],
        ["5. Conversation Setup", "app/services/chat_service.py", "_get_or_create_conversation() creates a new Conversation row titled 'Is hiking in Manali safe tomorrow?' owned by current_user.id. _fetch_conversation_history() loads recent turns."],
        ["6. Intent Routing", "app/llm/router.py", "route_query() analyzes text: extract_location() finds 'Manali' (in KNOWN_CITIES); extract_date_intent() detects 'tomorrow' (forecast_days=2); extract_category_hint() flags 'hiking_safety'; rule 2 triggers RouteSource.BOTH."],
        ["7. Live Weather Fetch", "app/weather/service.py", "get_daily_forecast('Manali', days=2) checks Redis cache key 'weather:daily:manali:2'. On miss: geocode_city('Manali') returns lat 32.24, lon 77.19; fetch_daily_forecast() calls Open-Meteo; logs to weather_api_logs; stores in Redis with 600s TTL."],
        ["8. Vector Retrieval", "app/rag/retrieval.py", "retrieve_relevant_chunks('Is hiking in Manali safe tomorrow?') embeds query via all-MiniLM-L6-v2; executes pgvector cosine similarity (<=>); matches mountain_hiking_weather_safety.pdf chunks (similarity >= 0.30)."],
        ["9. Prompt Assembly", "app/llm/prompts.py", "build_user_prompt() bundles: <live_weather> (Manali tomorrow temp/rain/wind), <knowledge_context> (mountain altitude, hypothermia, lightning rules), and strict system instructions (do not declare 'it is safe')."],
        ["10. Gemini Generation", "app/llm/generator.py", "generate_response() sends prompt to gemini-3.5-flash-lite via google-genai SDK wrapped in run_in_threadpool. Returns structured response with citations and advice."],
        ["11. DB Save & Audit", "app/services/chat_service.py", "_save_message_and_respond() saves Message(question, answer) to DB, logs AuditLog(action='chat_message'), calculates total latency_ms, returns ChatResponse."],
        ["12. UI Rendering", "frontend/streamlit_app.py", "Streamlit receives HTTP 200, parses ChatResponse, displays answer, confidence badge ('high'), latency, and clickable citation expanders."]
    ]

    table_rows = [[
        Paragraph("<b>Step & Stage</b>", TableHeader),
        Paragraph("<b>Code File Location</b>", TableHeader),
        Paragraph("<b>Exact Execution Logic & State Transition</b>", TableHeader)
    ]]
    for s in deep_steps:
        table_rows.append([
            Paragraph(s[0], TableCellBold),
            Paragraph(s[1], TableCellCode),
            Paragraph(s[2], TableCell)
        ])

    t = Table(table_rows, colWidths=[90, 130, 300])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_BG_ALT]),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("4.2 Short Request Flows for Key Operations", H2))

    flows = [
        ("Login Flow", "Client POST /api/v1/auth/login with {email, password} --> SlowAPI checks rate limit (5/min) --> User looked up in DB by email --> password.verify_password(input, user.password_hash) checks Argon2id hash --> jwt_handler creates 30m access_token and 7d refresh_token --> Returns TokenPair (HTTP 200)."),
        ("Weather-Only Flow", "User asks 'What is the temperature in Delhi?' --> Router flags RouteSource.WEATHER with location='Delhi' --> Checks Redis cache 'weather:current:delhi' --> On hit, returns cached metrics instantly (<5ms); on miss, calls Open-Meteo API, logs to weather_api_logs, caches result --> Gemini synthesizes concise observation briefing --> Saved to messages table."),
        ("RAG-Only Flow", "User asks 'What precautions should be taken during a heatwave?' --> Router flags RouteSource.RAG with category='heatwave' (no city mentioned) --> Query converted to 384-dim vector --> pgvector executes cosine similarity search over document_chunks table --> Top 5 chunks formatted into XML <knowledge_context> --> Gemini synthesizes answer with document citations."),
        ("Out-of-Scope Fast-Path", "User asks 'What is Apple's stock price?' --> Router checks OUT_OF_SCOPE_TERMS ('stock') and assigns RouteSource.NEITHER --> Short-circuits immediately in chat_service without calling weather API, vector DB, or Gemini LLM --> Returns canned polite refusal in <15ms, saving API costs and database load."),
        ("Clarification Fast-Path", "User asks 'Will it rain tomorrow?' --> Router detects weather intent ('rain', 'tomorrow') but extract_location() finds no city --> Assigns RouteSource.CLARIFICATION --> Short-circuits and prompts user: 'Could you please specify which city or location you want weather details for?' (Latency <10ms)."),
        ("Weather API Failure Graceful Degradation", "User asks for weather in an unreachable location or Open-Meteo returns HTTP 502/504 --> weather_service catches WeatherAPIError and logs 502/504 in weather_api_logs --> Returns structured error message: 'Weather data could not be retrieved from Open-Meteo' --> System does not crash; returns HTTP 200 with clear explanation."),
        ("Evaluation Benchmark Run", "Evaluator calls POST /api/v1/evaluation/run --> require_evaluator verifies role --> evaluator.py loads 15 test cases from dataset.json --> For each case, invokes process_chat_message() --> metrics.py computes routing (0-1), retrieval (0-1), and answer scores (0-1) --> Persists 15 rows to evaluation_results table --> Generates evaluation_report.md.")
    ]

    for title, desc in flows:
        flow_p = Paragraph(f"• <b>{title}:</b> {desc}", BulletText)
        story.append(flow_p)

    story.append(Spacer(1, 10))
    return story
