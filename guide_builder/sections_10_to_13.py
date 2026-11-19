"""
Sections 10 to 13 of the Study Guide:
10. Intent Routing & LLM Generation Engine
11. Evaluation Benchmark & Pytest Test Suite
12. Problems, Bugs & Fixes (From Our Development Journey)
13. Design Decisions & Architectural Trade-offs
"""
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
from reportlab.lib import colors
from guide_builder.styles import (
    H1, H2, H3, Body, BodyBold, BodySmall, BulletText, TableHeader, TableCell, TableCellBold, TableCellCode,
    PRIMARY, PRIMARY_LIGHT, ACCENT, ROW_BG_ALT, BORDER_COLOR, make_callout, make_code_box
)

def build_section_10():
    story = []
    story.append(Paragraph("10. Intent Routing & LLM Generation Engine", H1))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))
    
    routing_desc = (
        "The system avoids the latency and expense of calling an LLM for classification by employing a high-performance, "
        "deterministic regex and rule-based router in <code>app/llm/router.py</code>. The router evaluates input in under 0.1ms "
        "across seven strictly ordered rules:<br/><br/>"
        "<b>1. The 7 Ordered Routing Rules:</b><br/>"
        "• <b>Rule 1 (Definitional $\\rightarrow$ RAG):</b> Matches 'what is', 'define', 'explain' paired with weather/safety terms without location (e.g., 'What is a heatwave?').<br/>"
        "• <b>Rule 2 (Location + Hazard $\\rightarrow$ BOTH):</b> Location exists AND safety terms (heatwave, cyclone, alert, hiking) exist (e.g., 'Is hiking in Manali safe tomorrow?').<br/>"
        "• <b>Rule 3 (Weather without Location $\\rightarrow$ CLARIFICATION):</b> Weather terms present ('rain', 'forecast') but no city detected (e.g., 'Will it rain tomorrow?'). Prompts user for city.<br/>"
        "• <b>Rule 4 (General Precautions $\\rightarrow$ CLARIFICATION):</b> Queries asking for 'precautions' without specifying city or hazard type.<br/>"
        "• <b>Rule 5 (Hazard without Location $\\rightarrow$ RAG):</b> Asks for safety guidelines without a specific city (e.g., 'What precautions should be taken in a cyclone?').<br/>"
        "• <b>Rule 6 (Location Present $\\rightarrow$ WEATHER):</b> City name is detected paired with weather terms, date intents, OR is a standalone city query (e.g., 'delhi', 'mumbai today', 'badmer weather').<br/>"
        "• <b>Rule 7 (Out-of-Scope $\\rightarrow$ NEITHER):</b> Unrelated queries (stocks, crypto, recipes, movies). Short-circuits immediately.<br/><br/>"
        "<b>2. Entity Extraction Engine:</b><br/>"
        "• <b>Location Extraction:</b> Multi-stage pipeline checking: (1) 46 known cities with word boundary regex; (2) possessive forms ('Delhi\\'s'); (3) Hindi colloquial phrases ('Jaipur me'); (4) prefix/postfix patterns ('badmer weather', 'weather in Pune'); (5) prepositional matches ('in/at &lt;city&gt;').<br/>"
        "• <b>Date Intent Extraction:</b> Detects 'today', 'now', 'tomorrow' (2 days), 'this evening' (hourly flag), 'day after tomorrow' (3 days), 'next week' (7 days), and flags 'beyond_range' (>16 days).<br/><br/>"
        "<b>3. Prompt Architecture & Anti-Hallucination Design:</b><br/>"
        "Prompts are assembled in <code>app/llm/prompts.py</code> using strict XML-encapsulated context:<br/>"
        "• <code>&lt;conversation_history&gt;</code>: Past 4 Q&A turns for contextual continuity.<br/>"
        "• <code>&lt;live_weather&gt;</code>: Live temperature, humidity, wind, and precipitation metrics from Open-Meteo.<br/>"
        "• <code>&lt;knowledge_context&gt;</code>: Top-5 retrieved document chunks with source metadata.<br/>"
        "• <code>&lt;official_alert_directive&gt;</code>: Injected when official alerts are queried, requiring the explicit disclaimer: <i>'Live numerical weather metrics do not constitute official government weather alerts.'</i><br/>"
        "• <b>Behavioral Guardrails:</b> The system prompt explicitly instructs Gemini: (1) Never fabricate temperatures; (2) Never declare 'it is safe' for high-risk mountain activities; (3) State 'data unavailable' if metrics are missing; (4) Treat XML tags as passive data to prevent prompt injection.<br/>"
        "• <b>Generation Parameters:</b> Executed via Gemini 3.5 Flash Lite at <b>temperature 0.2</b> to minimize creative drift and maximize factual fidelity."
    )
    story.append(Paragraph(routing_desc, Body))
    story.append(Spacer(1, 10))
    return story

def build_section_11():
    story = []
    story.append(Paragraph("11. Evaluation Benchmark & Pytest Test Suite", H1))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))
    
    eval_desc = (
        "The project implements a rigorous, dual-layer verification system: an automated 15-question live benchmark "
        "and a 37-test hermetic Pytest test suite.<br/><br/>"
        "<b>1. The 15 Official Benchmark Questions (dataset.json):</b><br/>"
        "• Q1–Q3 (Live Weather): Delhi current temp, Bangalore rain probability, Mumbai tomorrow forecast.<br/>"
        "• Q4–Q6 (Pure RAG): Heatwave definition, IMD orange alert meaning, Cyclone evacuation precautions.<br/>"
        "• Q7–Q9 (Hybrid BOTH): Manali hiking safety tomorrow, Delhi elderly heatwave precautions, Pune rain + umbrella advisory.<br/>"
        "• Q10 (Official Alert): Mumbai weather alert status with mandatory non-equivalence disclaimer.<br/>"
        "• Q11–Q12 (Negative Tests): Misspelled city 'Delhii' (geocoding error) and out-of-range date (date validation error).<br/>"
        "• Q13 (Terminology): Cyclone vs hurricane vs typhoon regional definition comparison.<br/>"
        "• Q14 (Out-of-Scope): Apple stock price (verifies polite refusal without calling LLM).<br/>"
        "• Q15 (Ambiguity): Vague question missing city and hazard (verifies clarification prompt).<br/><br/>"
        "<b>2. Deterministic Scoring Formulas (metrics.py):</b><br/>"
        "• <b>Routing Score:</b> $1.0$ (exact route + location), $0.85$ (route match, location mismatch), $0.20$ (route mismatch, location match), $0.0$ (both wrong).<br/>"
        "• <b>Retrieval Score:</b> Evaluates category alignment (60%) and citation URL integrity (40%). Returns None for non-RAG routes.<br/>"
        "• <b>Answer Quality Score:</b> Weighted sum across 4 criteria: (1) Keyword coverage (40%); (2) Source citations (30%); (3) Official alert disclaimer (15%); (4) Anti-hallucination numerical grounding check (15%) verifying cited temperatures match Open-Meteo observations.<br/><br/>"
        "<b>3. Live Benchmark Results (Run ID: run_20261118_221106_e02571):</b>"
    )
    story.append(Paragraph(eval_desc, Body))
    story.append(Spacer(1, 4))

    benchmark_rows = [
        ["Metric", "Official Score", "Rubric Threshold", "Status"],
        ["Overall Test Pass Rate", "15 / 15 (100.0%)", ">= 80.0%", "PASS"],
        ["Average Routing Score", "1.000 / 1.000", ">= 0.900", "PASS"],
        ["Average Retrieval Score", "1.000 / 1.000", ">= 0.800", "PASS"],
        ["Average Answer Quality", "0.972 / 1.000", ">= 0.800", "PASS"],
        ["Average Latency", "4,278 ms", "<= 2,500 ms", "Review (Internet API)"],
        ["P95 Latency", "12,661 ms", "<= 4,000 ms", "Review (Cold Starts)"],
    ]
    t = Table([[Paragraph(f"<b>{c}</b>", TableHeader if i==0 else TableCellBold if j==0 else TableCell) for j, c in enumerate(row)] for i, row in enumerate(benchmark_rows)], colWidths=[150, 120, 130, 120])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_BG_ALT]),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    test_desc = (
        "<b>4. Hermetic Pytest Suite (37 Tests Passed in 6.99s):</b><br/>"
        "• <code>tests/test_api.py</code> (2 tests): Root greeting and DB healthcheck.<br/>"
        "• <code>tests/test_auth.py</code> (9 tests): Registration, duplicate emails, password verification, token revocation, RBAC, 429 limiter.<br/>"
        "• <code>tests/test_chat.py</code> (4 tests): Fast-path refusals, clarification prompts, error handling, end-to-end chat synthesis.<br/>"
        "• <code>tests/test_database.py</code> (4 tests): User data isolation, message pagination, pgvector cosine vector math.<br/>"
        "• <code>tests/test_evaluation.py</code> (4 tests): Scoring formula unit tests and evaluator role restrictions.<br/>"
        "• <code>tests/test_rag.py</code> (4 tests): Text cleaning, chunk boundaries, document ingestion, similarity threshold filtering.<br/>"
        "• <code>tests/test_router.py</code> (4 tests): Substring boundary collision edge cases, all 15 dataset questions.<br/>"
        "• <code>tests/test_weather.py</code> (6 tests): Geocoding, Open-Meteo client, cache hit/miss count, date range validation.<br/>"
        "All tests run inside isolated database transactions rolled back after each test, guaranteeing zero test state leakage."
    )
    story.append(Paragraph(test_desc, Body))
    story.append(Spacer(1, 10))
    return story

def build_section_12():
    story = []
    story.append(Paragraph("12. Problems, Bugs & Fixes (From Our Development Journey)", H1))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph(
        "During the construction, containerization, and evaluation of this system, we encountered several authentic engineering hurdles. "
        "Reviewing these prepares you to answer interview questions like <i>'What was the hardest bug you solved?'</i> or "
        "<i>'Tell me about a design challenge you faced.'</i>",
        Body
    ))

    bugs_data = [
        ("Gemini 2.5 Model Deprecation (HTTP 404)",
         "Google deprecated 'gemini-2.5-flash' for new API users, causing 404 Model Not Found errors.",
         "Upgraded model configuration to 'gemini-3.5-flash-lite' using the modern google-genai SDK. Eliminated deprecation warnings and restored generation.",
         "Cloud AI models evolve rapidly; decouple model names into environment variables (LLM_MODEL) rather than hardcoding strings in generator code."),

        ("Windows Asyncio SSL Handshake Timeout",
         "On Windows Python 3.13, asyncio Proactor loop caused client.aio.models.generate_content to hang indefinitely on SSL handshake.",
         "Wrapped synchronous client.models.generate_content in Starlette's run_in_threadpool, delegating execution to a worker thread off the main event loop.",
         "Windows asyncio Proactor loop has documented SSL socket bugs with certain HTTP/2 transports; worker thread pools provide rock-solid async isolation."),

        ("Docker 1.46GB Build Context & DNS Timeouts",
         "docker compose up --build copied the entire venv folder, .git repo, and cache into the Docker daemon, exhausting bandwidth and triggering pip DNS failure.",
         "Authored a comprehensive .dockerignore excluding venv/, .git/, and .env; added --default-timeout=120 and --retries=5 to pip install.",
         ".dockerignore is essential for container security and performance; never allow secrets (.env) or local host venvs into image build contexts."),

        ("Docker Host Port 5433 Collision",
         "docker compose failed to bind port 5433 with error 'port is already allocated'.",
         "Discovered an orphan container (weatherintelligenceproject-postgres-1) holding port 5433. Stopped it and wired compose to the existing pgvector volume.",
         "Always check 'docker ps' for orphan containers from earlier project sessions when external host port bindings collide."),

        ("Streamlit Container Running Backend Uvicorn",
         "The frontend container was executing entrypoint.sh default command (uvicorn), listening on port 8000 instead of running Streamlit on 8501.",
         "Updated entrypoint.sh with 'if [ \"$#\" -gt 0 ]; then exec \"$@\"; fi' and set entrypoint: ['streamlit', 'run', 'frontend/streamlit_app.py', ...] in compose.",
         "Entrypoint shell scripts must always support argument pass-through (exec \"$@\") to allow containers sharing an image to run different entry commands."),

        ("City-Only Queries Intercepted ('delhi')",
         "When user entered 'delhi', the router expected explicit keywords like 'weather' and treated the city as out-of-scope, returning a canned refusal.",
         "Enhanced Rule 6 in router.py: if a known location is detected and query length is <= 2 words without negative terms, classify as RouteSource.WEATHER.",
         "User intent in domain-specific assistants is often laconic (e.g., just typing a city name); guardrails must accommodate natural conversational shorthand."),

        ("Hinglish Queries Ignored ('Jaipur me barish ha kya')",
         "Colloquial Hindi terms ('barish', 'mausam') were missing from keyword sets, causing valid weather questions to be rejected as out-of-scope.",
         "Added Hindi weather vocabulary ('barish', 'baarish', 'mausam', 'garmi', 'sardi', 'thand') and regex patterns for '<city> me'.",
         "Real-world users in multicultural regions frequently converse in hybrid languages; domain routers must include colloquial vocabulary."),

        ("Geocoding Failure on City Spelling ('badmer weather')",
         "Open-Meteo geocoding only indexes official spelling 'Barmer', returning 404 Location Not Found for 'badmer'.",
         "Implemented CITY_ALIASES dictionary in geocoding.py mapping 'badmer' -> 'Barmer', 'bombay' -> 'Mumbai', 'calcutta' -> 'Kolkata'.",
         "External geocoding databases often adhere to strict colonial or bureaucratic spellings; local alias mapping layers are vital for resilience."),

        ("Cache Visibility in Swagger UI ('cached': true/false)",
         "User tested weather in Swagger and asked where to verify Redis caching. The JSON response showed latency but no explicit boolean flag.",
         "Added 'cached': False on initial Open-Meteo fetches and 'cached': True on Redis cache hits across current, daily, and hourly weather endpoints.",
         "APIs should be self-describing; exposing explicit operational metadata makes system behavior transparent for testing and evaluation.")
    ]

    table_rows = [[
        Paragraph("<b>Hurdle & Symptom</b>", TableHeader),
        Paragraph("<b>Root Cause Analysis</b>", TableHeader),
        Paragraph("<b>Engineering Fix Applied</b>", TableHeader),
        Paragraph("<b>Key Takeaway for Interview</b>", TableHeader)
    ]]
    for b in bugs_data:
        table_rows.append([
            Paragraph(b[0], TableCellBold),
            Paragraph(b[1], TableCell),
            Paragraph(b[2], TableCell),
            Paragraph(b[3], TableCell)
        ])

    t = Table(table_rows, colWidths=[105, 135, 145, 135])
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

def build_section_13():
    story = []
    story.append(Paragraph("13. Design Decisions & Architectural Trade-offs", H1))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph(
        "Every architectural choice involves balancing latency, complexity, cost, and developer productivity. "
        "Here is the rationale and trade-off analysis for each core technology in the stack:",
        Body
    ))

    tradeoffs = [
        ["FastAPI vs. Flask / Django",
         "Chose FastAPI for native asynchronous support (asyncio), automatic OpenAPI/Swagger generation, and strict runtime data validation via Pydantic v2.",
         "Flask requires extensive third-party plugins for validation and async; Django is heavyweight and introduces unnecessary ORM overhead for lightweight microservices."],

        ["PostgreSQL + pgvector vs. Pinecone / Chroma",
         "Chose pgvector to keep relational entities (users, conversations, audit logs) and vector embeddings in a single ACID-compliant database instance.",
         "Managed vector databases (Pinecone) introduce external network hops, vendor lock-in, and synchronization complexity across dual databases."],

        ["all-MiniLM-L6-v2 vs. OpenAI text-embedding-3",
         "Chose all-MiniLM-L6-v2 for 100% local, on-premise execution at $0 cost and ~15ms latency per chunk.",
         "Cloud embeddings (OpenAI) charge per token, introduce network latency, and expose sensitive disaster and user queries over external internet connections."],

        ["Open-Meteo vs. OpenWeatherMap",
         "Chose Open-Meteo because it is free for non-commercial use, requires no API key, and provides structured hourly and 16-day daily forecast models.",
         "OpenWeatherMap requires credit card registration, enforces strict minute quotas on free tiers, and returns nested payloads requiring custom parsing."],

        ["Redis with In-Memory Fallback vs. Memcached",
         "Chose Redis for rich data structures, string key TTLs, and container availability; designed custom CacheService with automatic fallback to Python memory dict.",
         "Memcached lacks built-in persistence primitives and does not support complex caching topologies as cleanly as Redis."],

        ["Gemini 3.5 Flash Lite vs. GPT-4o-mini",
         "Chose Gemini 3.5 Flash Lite for fast sub-second token generation, high reliability, and generous rate limits via the modern google-genai SDK.",
         "Larger models (GPT-4o) introduce 3–5x higher latency and expensive per-token billing without measurable accuracy gains on structured RAG synthesis."],

        ["Deterministic Regex Router vs. LLM Router",
         "Chose deterministic regex and keyword rule routing executing in 0.1ms at $0 cost with 100.0% reproducible classification accuracy.",
         "Using an LLM to classify user intent adds 600–1200ms latency, incurs token costs on every message, and risks nondeterministic routing mistakes."]
    ]

    table_rows = [[
        Paragraph("<b>Architectural Decision</b>", TableHeader),
        Paragraph("<b>Why Chosen (Benefits)</b>", TableHeader),
        Paragraph("<b>Alternative Considered & Trade-off</b>", TableHeader)
    ]]
    for tr in tradeoffs:
        table_rows.append([
            Paragraph(tr[0], TableCellBold),
            Paragraph(tr[1], TableCell),
            Paragraph(tr[2], TableCell)
        ])

    t = Table(table_rows, colWidths=[120, 200, 200])
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
