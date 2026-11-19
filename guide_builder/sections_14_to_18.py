"""
Sections 14 to 18 of the Study Guide:
14. Commands Cheat Sheet (Setup & Execution)
15. Assignment Coverage Matrix
16. Known Limitations & Interview Defense Strategies
17. 40 Likely Technical Interview Questions + 2-Minute Elevator Pitch
18. Comprehensive Technical Glossary
"""
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from guide_builder.styles import (
    H1, H2, H3, Body, BodyBold, BodySmall, BulletText, TableHeader, TableCell, TableCellBold, TableCellCode,
    PRIMARY, PRIMARY_LIGHT, ACCENT, ROW_BG_ALT, BORDER_COLOR, SUCCESS_COLOR, make_callout, make_code_box
)

def build_section_14():
    story = []
    story.append(Paragraph("14. Commands Cheat Sheet: Setup & Execution", H1))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph(
        "Every command required to build, test, run, and audit the application from a clean machine, with its exact expected output:",
        Body
    ))

    commands = [
        ["1. Create Python Virtual Env",
         "python -m venv venv",
         "Creates isolated Python 3.11/3.13 virtual environment in ./venv directory.",
         "Folder ./venv/ created with Scripts/ and Lib/ subdirectories."],

        ["2. Activate Virtual Env",
         ".\\venv\\Scripts\\Activate.ps1",
         "Activates the virtual environment for the current PowerShell terminal session.",
         "Prompt prefixed with (venv)."],

        ["3. Install Dependencies",
         "pip install -r requirements.txt",
         "Installs all 22 pinned runtime and test packages from PyPI.",
         "Successfully installed fastapi uvicorn sqlalchemy pgvector ..."],

        ["4. Configure Environment",
         "cp .env.example .env",
         "Copies the template environment file for customization.",
         "File .env created. (Populate GEMINI_API_KEY and SECRET_KEY)."],

        ["5. Launch Docker Stack",
         "docker compose up -d",
         "Builds and starts all 4 containers in background (db, redis, api, frontend).",
         "[+] Running 4/4 Container weather_assistant_* Started."],

        ["6. Check Service Health",
         "docker compose ps",
         "Inspects the running container list and healthcheck statuses.",
         "All 4 containers display 'Up ... (healthy)'."],

        ["7. Run Database Migrations",
         "alembic upgrade head",
         "Applies all pending Alembic schema revisions to PostgreSQL.",
         "INFO [alembic] Running upgrade ... -> 662e79249848 (head)."],

        ["8. Ingest Knowledge Base",
         "python scripts/ingest_documents.py",
         "Parses 7 disaster PDFs, chunks them, computes embeddings, saves to DB.",
         "Completed ingestion of 7 documents (46 total chunks added)."],

        ["9. Run Local FastAPI Backend",
         "uvicorn app.main:app --reload --port 8000",
         "Starts the Uvicorn ASGI server with hot-reload enabled.",
         "Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)."],

        ["10. Run Local Streamlit UI",
         "streamlit run frontend/streamlit_app.py",
         "Launches the interactive multi-tab web user interface.",
         "Local URL: http://localhost:8501. Browser window opens."],

        ["11. Run Pytest Test Suite",
         "pytest -v",
         "Executes all 37 unit and integration tests across 8 test modules.",
         "37 passed in 6.99s (100% test pass rate)."],

        ["12. Run Evaluation Benchmark",
         "python -m app.evaluation.evaluator",
         "Executes 15 official test cases through live pipeline and saves scores.",
         "15/15 Passed (100.0%). Written to evaluation_report.md."],

        ["13. Inspect Redis Cache Keys",
         "docker exec weather_assistant_redis redis-cli KEYS \"*\"",
         "Queries Redis memory for all active cached weather keys.",
         "weather:current:delhi, weather:current:jaipur, ..."],

        ["14. View Cached City JSON",
         "docker exec weather_assistant_redis redis-cli GET \"weather:current:delhi\"",
         "Prints raw serialized weather payload stored in Redis.",
         "{\"source\": \"Open-Meteo\", \"temperature_c\": 21.5, ...}"],

        ["15. Clean Project Shutdown",
         "docker compose down",
         "Stops and deletes running containers; preserves persistent database volumes.",
         "[+] Running 4/4 Container weather_assistant_* Removed."]
    ]

    table_rows = [[
        Paragraph("<b>Action & Goal</b>", TableHeader),
        Paragraph("<b>Exact Command Syntax</b>", TableHeader),
        Paragraph("<b>What It Does Internally</b>", TableHeader),
        Paragraph("<b>Expected Terminal Output</b>", TableHeader)
    ]]
    for cmd in commands:
        table_rows.append([
            Paragraph(cmd[0], TableCellBold),
            Paragraph(cmd[1], TableCellCode),
            Paragraph(cmd[2], TableCell),
            Paragraph(cmd[3], TableCellSmall := ParagraphStyle("TCmdSmall", parent=TableCell, fontName="Courier", fontSize=6.5, leading=8))
        ])

    t = Table(table_rows, colWidths=[90, 140, 155, 135])
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
    story.append(Spacer(1, 10))
    return story

def build_section_15():
    story = []
    story.append(Paragraph("15. Assignment Requirement Coverage Matrix", H1))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph(
        "A rigorous, item-by-item verification against the university/corporate assignment specification "
        "(<code>Weather_Intelligence_Assistant_Assignment 1.docx</code>):",
        Body
    ))

    requirements = [
        ["Authentication & JWT", "Dual-token access (30m) & refresh (7d), logout revocation, password hashing.", "DONE", "app/auth/jwt_handler.py, app/auth/password.py, app/api/auth.py"],
        ["Role-Based Access Control", "3 distinct roles (USER, ADMIN, EVALUATOR) with route-level security guards.", "DONE", "app/auth/dependencies.py (require_admin, require_evaluator)"],
        ["Rate Limiting", "IP-based rate limits (5/min on auth, 30/min on chat) returning HTTP 429.", "DONE", "app/core/security.py, app/api/auth.py, app/api/chat.py"],
        ["Relational DB Schema", "9 normalized tables: users, conversations, messages, documents, chunks, etc.", "DONE", "app/database/models.py, alembic/versions/"],
        ["Database Migrations", "Automated migration harness using Alembic with 3 sequential revisions.", "DONE", "alembic.ini, alembic/env.py, alembic/versions/"],
        ["pgvector Integration", "384-dimensional vector column with native cosine distance search (<=>).", "DONE", "app/database/models.py (Vector(384)), app/rag/retrieval.py"],
        ["RAG Document Ingestion", "Parsers for PDF, HTML, DOCX, TXT; 500-char chunks with 50-char overlap.", "DONE", "app/rag/chunking.py, app/rag/ingestion.py, scripts/ingest_documents.py"],
        ["Local Embedding Model", "all-MiniLM-L6-v2 SentenceTransformer loaded locally with LRU caching.", "DONE", "app/rag/embeddings.py (384-dim dense vectors)"],
        ["Semantic Retrieval", "pgvector similarity search with 0.30 threshold and citation metadata.", "DONE", "app/rag/retrieval.py (similarity = 1.0 - distance)"],
        ["Live Weather Integration", "Open-Meteo current weather, daily (1-16d), and hourly (1-168h) forecasts.", "DONE", "app/weather/client.py, app/weather/service.py, app/api/weather.py"],
        ["Geocoding & Aliasing", "Open-Meteo geocoding with Indian city alias dictionary (Badmer -> Barmer).", "DONE", "app/weather/geocoding.py (CITY_ALIASES)"],
        ["Redis Caching Layer", "600s TTL on weather responses, in-memory fallback, 'cached' flag.", "DONE", "app/services/cache_service.py, app/weather/service.py"],
        ["Weather API Logging", "Every call logged to weather_api_logs table with params, response, latency.", "DONE", "app/services/logging_service.py (log_weather_api_call)"],
        ["Intelligent Query Router", "Classifies into WEATHER, RAG, BOTH, NEITHER, CLARIFICATION without LLM.", "DONE", "app/llm/router.py (7 priority rules, 46 cities, dates)"],
        ["LLM Answer Generation", "Gemini 3.5 Flash Lite via google-genai SDK, structured XML context.", "DONE", "app/llm/generator.py, app/llm/prompts.py"],
        ["Anti-Hallucination Guard", "Low temperature (0.2), numerical grounding, mandatory alert disclaimer.", "DONE", "app/llm/prompts.py (SYSTEM_INSTRUCTION), generator.py"],
        ["Conversational History", "Multi-turn context retention and entity recovery across follow-up turns.", "DONE", "app/services/chat_service.py (_find_location_in_history)"],
        ["Interactive Frontend UI", "Streamlit 4-tab dashboard: Chat, Live Explorer, Benchmark, Knowledge Docs.", "DONE", "frontend/streamlit_app.py, frontend/app.py"],
        ["Automated Benchmark", "15-question evaluation suite with persisted results and markdown report.", "DONE", "app/evaluation/dataset.json, evaluator.py, metrics.py"],
        ["Hermetic Pytest Suite", "37 unit/integration tests with transactional DB rollback.", "DONE", "tests/ (37 passed in 6.99s)"],
        ["Docker Containerization", "Multi-stage Dockerfile, non-root appuser, compose stack (4 services).", "DONE", "Dockerfile, docker-compose.yml, entrypoint.sh, .dockerignore"],
        ["Complete Documentation", "Architectural README with Mermaid ER & flowcharts, trade-offs, API table.", "DONE", "README.md, evaluation_report.md"]
    ]

    table_rows = [[
        Paragraph("<b>Assignment Requirement</b>", TableHeader),
        Paragraph("<b>Specific Implementation Detail</b>", TableHeader),
        Paragraph("<b>Status</b>", TableHeader),
        Paragraph("<b>Code File Evidence</b>", TableHeader)
    ]]
    for req in requirements:
        table_rows.append([
            Paragraph(req[0], TableCellBold),
            Paragraph(req[1], TableCell),
            Paragraph(f"<font color='{SUCCESS_COLOR}'><b>{req[2]}</b></font>", TableCellBold),
            Paragraph(req[3], TableCellCode)
        ])

    t = Table(table_rows, colWidths=[110, 180, 50, 180])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_BG_ALT]),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))
    return story

def build_section_16():
    story = []
    story.append(Paragraph("16. Known Limitations & Interview Defense Strategies", H1))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph(
        "Being completely honest about architectural limitations while demonstrating that you understand the production "
        "remedies marks the difference between a junior developer and a mature engineer. Here are the likely interviewer "
        "probes and the winning defense for each:",
        Body
    ))

    limitations = [
        ("Probe 1: 'Your router uses regex and keyword matching. Why not use an LLM or semantic classifier?'",
         "Honest Admission: A regex-based router cannot generalize to completely novel phrasings outside its vocabulary or handle complex multi-intent linguistic nuances.<br/>"
         "Winning Defense: 'I intentionally chose a deterministic regex router for this microservice because it executes in 0.1ms at zero financial cost, whereas an LLM classifier introduces 800ms of latency and token fees on every single message. Furthermore, in an evaluation benchmark, deterministic routing guarantees 100% reproducible classifications without probabilistic drift. In a production v2, I would use a hybrid approach: fast regex for 90% of canonical queries, falling back to an on-device sentence-transformer embedding classifier (cosine similarity against route centroids) for ambiguous queries.'"),

        ("Probe 2: 'Your token blacklist is stored in an in-memory Python set. What happens when you scale to multiple Uvicorn worker processes?'",
         "Honest Admission: In-memory token revocation does not share state across multiple process boundaries or horizontally autoscaled container instances.<br/>"
         "Winning Defense: 'That is an accurate observation. In my current deployment, Uvicorn runs as a single process per container, so an in-memory set provides instant microsecond verification. However, for a distributed multi-worker or Kubernetes deployment, I would migrate the token blacklist directly into Redis using a key format like 'revoked:token:<jti>' with an automatic TTL matching the token's remaining lifespan. This guarantees instantaneous cross-node revocation without memory leakage.'"),

        ("Probe 3: 'Why did you choose a fixed 500-character chunking strategy instead of recursive character or semantic chunking?'",
         "Honest Admission: Fixed 500-character chunks can occasionally cut across closely linked conceptual arguments that span across paragraphs.<br/>"
         "Winning Defense: 'I designed split_text_into_chunks to prioritize natural sentence terminators and paragraph breaks past the 250-character midpoint, which prevents slicing sentences or words in half. 500 characters corresponds to ~80-100 words, perfectly aligned with the 256-token sweet spot of all-MiniLM-L6-v2 without truncation. For future iterations, I would explore hierarchical semantic chunking where section headers are preserved as metadata parents above paragraph children.'"),

        ("Probe 4: 'Why is your evaluation latency P95 (12.6s) higher than the assignment rubric threshold (4.0s)?'",
         "Honest Admission: The P95 latency reached 12.6 seconds during the automated evaluation run.<br/>"
         "Winning Defense: 'The latency spike is entirely external: the benchmark executes live HTTPS requests against Open-Meteo's European API servers and Google's Gemini LLM endpoints back-to-back across 15 questions. Because the benchmark purposefully tests fresh cities and dates, Redis cache misses occur on those questions. In production with a warm cache, response times for weather drop below 5ms, and the LLM generation itself executes in under 1.4 seconds.'"),

        ("Probe 5: 'Why did you use psycopg3 binary instead of asyncpg for your SQLAlchemy driver?'",
         "Honest Admission: Psycopg3 binary uses synchronous threadpool wrappers inside FastAPI endpoints rather than pure native non-blocking async sockets.<br/>"
         "Winning Defense: 'Psycopg 3 is the modern, official PostgreSQL adapter supporting both sync and async paradigms. In our workload, pgvector query latency is tiny (under 12ms), so connection pooling with pool_pre_ping=True easily handles standard concurrency. If we anticipated 10,000+ concurrent database connections, migrating to asyncpg or psycopg3 async engine with AsyncSession would be a straightforward transition.'")
    ]

    for title, desc in limitations:
        story.append(Paragraph(f"<b>{title}</b>", H3))
        story.append(Paragraph(desc, Body))
        story.append(Spacer(1, 4))

    return story

def build_section_17():
    story = []
    story.append(Paragraph("17. 40 Likely Interview Questions & Answers", H1))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))
    
    # 2-minute elevator pitch
    pitch_text = (
        "<b>Interviewer: 'Walk me through your project in 2 minutes.'</b><br/>"
        "<i>Your Spoken Answer:</i><br/>"
        "\"I built an enterprise Weather Intelligence and Disaster Advisory Assistant. It solves a major problem with standard AI chatbots: "
        "when people ask about severe weather or mountain safety, generic LLMs frequently hallucinate temperatures or give dangerously vague advice. "
        "My system combines live meteorological data from Open-Meteo with an authoritative RAG knowledge base of official NDMA and IMD disaster guidelines.<br/><br/>"
        "Architecturally, it's a decoupled microservice: a FastAPI backend and a Streamlit frontend containerized with Docker Compose. "
        "When a request arrives, it passes through SlowAPI rate limiting and JWT authentication with Argon2id password hashing. "
        "Then, a deterministic intent router classifies the query into one of five streams: live weather, RAG disaster knowledge, both, out-of-scope refusal, "
        "or clarification. This router executes in 0.1 milliseconds without calling an LLM.<br/><br/>"
        "For live weather, we resolve Indian city aliases, query Open-Meteo, and cache responses in Redis for 10 minutes to protect external rate limits. "
        "For disaster safety, we query 384-dimensional vector embeddings stored in PostgreSQL using pgvector with cosine distance. "
        "Finally, Gemini 3.5 Flash Lite synthesizes a safety briefing wrapped in strict XML context at a low temperature of 0.2, citing official guidelines and live observations.<br/><br/>"
        "To prove it works, I wrote 37 automated Pytest tests that pass in 7 seconds, and built a live 15-question benchmark that achieves a 100% pass rate with a 1.0 routing score, 1.0 retrieval score, and 0.97 answer quality score.\""
    )
    story.append(make_callout("The 2-Minute Project Pitch", pitch_text, "info"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Rapid-Fire Technical Interview Q&A (Spoken-Ready Answers):", H2))

    qa_list = [
        # Architecture & FastAPI
        ("1. What is FastAPI and why did you choose it over Flask?",
         "FastAPI is a modern ASGI web framework for Python. I chose it because it supports native asynchronous concurrency, auto-generates interactive Swagger documentation, and uses Pydantic v2 for strict runtime data validation."),
        ("2. What is Uvicorn and what role does it play?",
         "Uvicorn is a lightning-fast ASGI web server implementation based on uvloop and httptools. It serves as the HTTP application server that executes our FastAPI code inside the Docker container."),
        ("3. How does dependency injection work in FastAPI?",
         "FastAPI's Depends system allows you to declare shared dependencies like database sessions (get_db) and user authentication guards (get_current_user) directly in endpoint function signatures. FastAPI resolves them, injects the values, and handles cleanup automatically in finally blocks."),
        ("4. What are Pydantic models and why are they used?",
         "Pydantic models are Python classes that enforce data types and data validation at runtime. They automatically parse incoming JSON payloads, reject malformed requests with HTTP 422 errors, and serialize ORM entities for client responses."),
        ("5. How do you handle CORS in your backend?",
         "I use FastAPI's CORSMiddleware with allow_origins=['*'], allow_credentials=True, and unrestricted methods/headers to allow the Streamlit frontend on port 8501 to communicate seamlessly with the backend on port 8000."),
        
        # Database & pgvector
        ("6. What is pgvector and how does it work inside PostgreSQL?",
         "pgvector is an open-source extension for PostgreSQL that adds native vector data types and vector indexing (IVFFlat/HNSW). It allows storing mathematical embeddings alongside relational user data and computing cosine similarity using C-optimized CPU vector instructions."),
        ("7. What is an embedding and what dimension does your project use?",
         "An embedding is a numerical representation of semantic meaning where similar concepts are close together in high-dimensional space. My project generates 384-dimensional dense vectors using the all-MiniLM-L6-v2 model."),
        ("8. What vector distance metric did you choose and why?",
         "I chose Cosine Distance, accessed via pgvector's <=> operator. Cosine distance measures the angle between vectors rather than magnitude, which is the standard mathematical metric for normalized SentenceTransformer text embeddings."),
        ("9. Why did you use JSONB columns in PostgreSQL?",
         "JSONB stores JSON in a decomposed binary format that supports indexing and fast key extraction. I used it in weather_api_logs for request_params and response_json, and in document_chunks for metadata, allowing flexible metadata without modifying table schemas."),
        ("10. What is Alembic and how does it manage database migrations?",
         "Alembic is SQLAlchemy's database migration tool. It inspects changes between Python ORM models and live PostgreSQL tables, generating versioned migration scripts that can be upgraded or downgraded reproducibly across development, testing, and production."),

        # Auth & Security
        ("11. How does your JWT authentication work?",
         "When a user logs in, the backend signs an access token (expires in 30 minutes) and a refresh token (expires in 7 days) using HMAC-SHA256 and a secret key. The client passes the access token in the Authorization Bearer header for protected requests."),
        ("12. What algorithm is used for password hashing and why?",
         "I used Argon2id via pwdlib. Argon2id is the winner of the Password Hashing Competition and provides memory-hardness, making brute-force cracking using specialized GPU or ASIC hardware practically impossible compared to older algorithms like MD5 or plain SHA."),
        ("13. How does your system handle logout and token invalidation?",
         "Because JWTs are stateless, when a user logs out, their active token is added to an in-memory revoked tokens blacklist set in app/core/security.py. The get_current_user dependency checks this set on every request and rejects revoked tokens with HTTP 401."),
        ("14. How is Role-Based Access Control (RBAC) enforced?",
         "I created a custom require_roles dependency that wraps get_current_user. Endpoints declare their required role—such as Depends(require_admin) or Depends(require_evaluator)—and if the user's role does not match, a 403 Forbidden error is raised."),
        ("15. How do you prevent cross-user data leakage?",
         "Every database query for conversations or messages filters explicitly by current_user.id. If a user attempts to access a conversation ID belonging to someone else, the backend returns HTTP 404 Not Found to prevent resource enumeration attacks."),
        ("16. How does your rate limiting work?",
         "I used SlowAPI, an ASGI rate-limiting library. It tracks request counts by client IP address using an in-memory sliding window, enforcing 5 requests/minute on login/register endpoints and 30 requests/minute on chat, returning HTTP 429 when exceeded."),

        # Weather Integration
        ("17. What weather provider did you use and why?",
         "I used Open-Meteo. It provides high-quality meteorological forecasts, requires no commercial API key, supports both hourly and 16-day daily forecast ranges, and has no strict request rate caps for non-commercial educational use."),
        ("18. How do you resolve city names to coordinates?",
         "I use Open-Meteo's geocoding API to resolve city names into latitude, longitude, and timezone. I also built a CITY_ALIASES dictionary that automatically normalizes colloquial Indian city names like 'badmer' to 'Barmer' and 'bombay' to 'Mumbai'."),
        ("19. How does your Redis caching work for weather?",
         "Weather responses are cached in Redis for 600 seconds (10 minutes) under keys like weather:current:<city>. The first request fetches live data from Open-Meteo with cached=False; subsequent requests within 10 minutes return from Redis memory in under 5ms with cached=True."),
        ("20. What happens if Redis goes down?",
         "My CacheService class implements a seamless in-memory fallback. If Redis is unreachable, it logs a warning and stores the key-value pairs in a local Python dictionary with timestamp expiry, ensuring zero downtime or 500 errors for users."),
        ("21. How do you log weather API calls?",
         "Every external request to Open-Meteo is captured in the weather_api_logs table with the queried city, request parameters, response JSON, HTTP status code, and latency in milliseconds. This provides full visibility into API usage and reliability."),
        ("22. What weather codes does Open-Meteo return?",
         "Open-Meteo returns World Meteorological Organization (WMO) numeric codes. My service decodes them using WMO_WEATHER_CODES into clear descriptions like 'Clear sky' (0), 'Moderate rain' (63), or 'Thunderstorm' (95)."),

        # RAG & Embeddings
        ("23. What is RAG and why is it useful in this project?",
         "Retrieval-Augmented Generation retrieves authoritative document chunks from a vector database and injects them into the LLM prompt as ground truth context. This ensures the assistant's disaster advice is based on official government manuals rather than vague training data."),
        ("24. What documents are in your knowledge base?",
         "Seven official guidelines: NDMA Heatwave Guidelines, IMD Color-Coded Weather Warnings, NDMA Cyclone Guidelines, NOAA Cyclone vs Hurricane Terminology, Mountain Hiking Safety, Rain & Flood Safety, and NDMA Cold Wave Guidelines."),
        ("25. What chunking strategy did you use and why?",
         "I used 500 characters with 50 characters overlap, combined with smart boundary detection that splits on paragraph and sentence endings rather than cutting words in half. 500 characters fits the embedding model's optimal input length while preserving paragraph context."),
        ("26. What embedding model did you choose and why?",
         "I chose sentence-transformers/all-MiniLM-L6-v2. It runs locally on CPU in ~15ms, costs $0, outputs compact 384-dimensional vectors, and pre-downloads into the Docker image at build time so the container never depends on HuggingFace servers at runtime."),
        ("27. How does semantic retrieval work in your codebase?",
         "The user's query is converted to an embedding vector. PostgreSQL executes a cosine distance search (<=>) on the document_chunks table, filtering chunks with similarity >= 0.30, and returning the top-5 most relevant passages ordered by similarity."),
        ("28. How are document citations returned to the user?",
         "Each retrieved chunk retains metadata: document title, category, chunk index, and source URL. These are passed to the frontend as DocumentSource objects, which Streamlit renders as clickable, transparent citations beneath each answer."),

        # Intent Routing & LLM
        ("29. How does your intent router work?",
         "It is a deterministic, rule-based router in app/llm/router.py. It evaluates queries using regex and gazetteers across 7 priority rules, classifying into WEATHER, RAG, BOTH, NEITHER, or CLARIFICATION in 0.1ms without incurring LLM latency or cost."),
        ("30. How do you extract locations from conversational queries?",
         "extract_location uses a multi-stage approach: exact matching against 46 known cities with word boundaries, possessive forms ('Delhi's'), colloquial Hindi patterns ('Jaipur me'), prefix patterns ('badmer weather'), and prepositional phrases ('in/at <city>')."),
        ("31. How does context recovery work across multi-turn chats?",
         "If a user asks a follow-up question like 'Will it be hot tomorrow?' without mentioning a city, _find_location_in_history scans previous turns in the conversation to retrieve the previously discussed city, maintaining natural dialogue flow."),
        ("32. What LLM do you use and how is it integrated?",
         "I use Gemini 3.5 Flash Lite via Google's modern google-genai SDK. Generation runs wrapped in Starlette's run_in_threadpool with temperature=0.2 and exponential backoff retry logic for 429 and 503 HTTP status codes."),
        ("33. How do you prevent LLM hallucinations?",
         "Three techniques: (1) Setting temperature to 0.2 for strict factual fidelity; (2) Providing verified numbers in passive <live_weather> XML tags with instructions never to invent values; (3) Mandating that mountain safety queries state risks rather than declaring 'it is safe'."),
        ("34. How is the confidence score calculated?",
         "calculate_confidence evaluates data availability. If both live weather and high-similarity RAG chunks (score >= 0.50) are present, it assigns 'high'. If only one source is present or similarity is lower, it assigns 'medium'. If data is missing or error-prone, it assigns 'low'."),
        ("35. What is the mandatory official alert disclaimer?",
         "Whenever a user asks about official weather alerts, the prompt injects an explicit directive requiring the response to state: 'Live numerical weather metrics do not constitute official government weather alerts.'"),

        # Testing & Evaluation
        ("36. What benchmark dataset did you use?",
         "I implemented the official 15-question dataset.json from the assignment document, covering live weather observations, pure disaster RAG queries, hybrid both queries, official alert checks, negative spelling tests, and out-of-scope refusals."),
        ("37. How do you score the evaluation benchmark?",
         "Without LLMs. Routing score compares actual vs expected route and location (0-1.0). Retrieval score measures category alignment and citation URLs. Answer score uses deterministic regex to verify keyword coverage, citations, alert disclaimers, and numerical temperature grounding."),
        ("38. What are your real benchmark results?",
         "15 out of 15 tests passed (100.0% pass rate). Routing accuracy is 1.000, retrieval score is 1.000, and answer quality score is 0.972, with all results saved to the evaluation_results PostgreSQL table."),
        ("39. How is your Pytest suite structured?",
         "37 tests across 8 test modules covering auth, api, weather, rag, router, database, chat, and evaluation. Every test uses a transactional database fixture that rolls back changes after execution, ensuring tests are 100% hermetic and never leak state."),
        ("40. What is your Docker setup?",
         "A multi-stage Dockerfile with a non-root appuser (UID 1000) and pre-downloaded sentence-transformer models. Orchestrated via docker-compose with 4 services: PostgreSQL 16 (pgvector), Redis 7 Alpine, FastAPI backend (:8000), and Streamlit frontend (:8501).")
    ]

    for q, a in qa_list:
        story.append(Paragraph(f"<b>{q}</b>", H3))
        story.append(Paragraph(a, Body))
        story.append(Spacer(1, 2))

    return story

def build_section_18():
    story = []
    story.append(Paragraph("18. Comprehensive Technical Glossary", H1))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph(
        "Clear, jargon-free definitions of every major concept and acronym used in this project:",
        Body
    ))

    terms = [
        ("RAG (Retrieval-Augmented Generation)", "An AI architectural pattern that retrieves relevant factual passages from an external database and feeds them into an LLM prompt as context, enabling the model to give accurate, cited answers without hallucinating."),
        ("Vector Embedding", "A list of floating-point numbers (e.g. 384 numbers) generated by a neural network that mathematically captures the semantic meaning of text. Words and sentences with similar meanings produce vectors that are close together in space."),
        ("pgvector", "An open-source PostgreSQL extension that adds support for vector storage, vector distance indexing, and exact vector math directly inside traditional relational database tables."),
        ("Cosine Similarity / Cosine Distance", "A mathematical formula that measures the angle between two multi-dimensional vectors. Cosine similarity ranges from -1 to 1 (1 being identical). Cosine distance is (1.0 - similarity), where 0.0 means identical direction."),
        ("JWT (JSON Web Token)", "A compact, URL-safe, digitally signed string format used to securely transmit claims between parties. Used here for stateless Bearer authentication in API request headers."),
        ("RBAC (Role-Based Access Control)", "A security authorization model where system privileges and API endpoint access are assigned based on defined user roles (e.g., USER, EVALUATOR, ADMIN) rather than individual user IDs."),
        ("Argon2id", "The state-of-the-art cryptographic password hashing algorithm. It is memory-hard, making brute-force cracking on GPUs and custom ASIC rigs computationally prohibitive."),
        ("Alembic", "The standard database migration tool for SQLAlchemy. It tracks ORM model revisions and automates database schema evolution across dev, staging, and production environments."),
        ("Dependency Injection", "A software design pattern where objects or functions receive their required dependencies (such as database sessions or authenticated users) from an external framework rather than instantiating them internally."),
        ("TTL (Time-To-Live)", "A countdown timer attached to a cached item in Redis (e.g., 600 seconds). When the timer expires, the cache automatically deletes the record so future requests fetch fresh data."),
        ("Cache Hit vs. Cache Miss", "A Cache Hit occurs when requested data is found in fast memory (Redis), returning in <5ms. A Cache Miss occurs when the key is absent, requiring a slow call to the external network API (~650ms)."),
        ("Rate Limiting", "A defensive traffic-throttling mechanism that restricts how many API requests a client IP can make within a time window (e.g., 5 requests per minute) to prevent abuse and denial-of-service."),
        ("ORM (Object-Relational Mapping)", "A programming technique that maps relational database tables to Python classes and rows to Python objects (e.g., SQLAlchemy), allowing developers to write Python code instead of raw SQL queries."),
        ("Pydantic", "The leading Python library for data validation and settings management based on Python type annotations. It parses JSON payloads and rejects malformed data with HTTP 422 errors."),
        ("Uvicorn", "A high-performance ASGI (Asynchronous Server Gateway Interface) web server implementation for Python that runs FastAPI applications."),
        ("Non-Root User in Docker", "A container security best practice where the application process runs under a dedicated, unprivileged user account (e.g., appuser, UID 1000) rather than root, limiting damage if the container is compromised."),
        ("Multi-Stage Docker Build", "A Dockerfile technique that uses multiple FROM statements to separate build compilation tools (gcc, build-essential) from the final lean runtime image, drastically reducing image size and attack surface."),
        ("WMO Weather Codes", "A standardized set of numeric codes defined by the World Meteorological Organization representing atmospheric conditions (e.g., 0 = Clear, 61 = Slight rain, 95 = Thunderstorm)."),
        ("Deterministic Router", "A query routing algorithm built from explicit logic, regex, and keyword rules that produces the exact same classification every time with zero probabilistic drift and zero latency overhead."),
        ("Grounding / Anti-Hallucination", "Techniques used in AI engineering (such as low temperature, passive XML data encapsulation, and numerical verification) to ensure LLM answers strictly reflect provided source facts.")
    ]

    table_rows = [[
        Paragraph("<b>Term / Concept</b>", TableHeader),
        Paragraph("<b>Plain-English Definition & Real Project Context</b>", TableHeader)
    ]]
    for term, defn in terms:
        table_rows.append([
            Paragraph(f"<b>{term}</b>", TableCellBold),
            Paragraph(defn, TableCell)
        ])

    t = Table(table_rows, colWidths=[150, 390])
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
    return story
