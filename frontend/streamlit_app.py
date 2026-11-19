import os
from typing import Any
import requests
import streamlit as st

# Configure page
st.set_page_config(
    page_title="Weather Intelligence & Advisory Assistant",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Constants & Defaults
DEFAULT_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000/api/v1")

# Initialize Session State
if "api_url" not in st.session_state:
    st.session_state.api_url = DEFAULT_API_URL
if "token" not in st.session_state:
    st.session_state.token = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []


def get_auth_headers() -> dict[str, str]:
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}


# ---------------------------------------------------------
# Sidebar: Auth & Configuration
# ---------------------------------------------------------
with st.sidebar:
    st.title("🌦️ Weather Intelligence")
    st.caption("Multimodal Meteorological & Safety Advisory")
    st.divider()

    # API Configuration
    st.subheader("⚙️ Backend Configuration")
    api_url = st.text_input("API Base URL", value=st.session_state.api_url)
    st.session_state.api_url = api_url.rstrip("/")

    st.divider()

    # User Authentication
    st.subheader("👤 User Account")
    if st.session_state.token:
        role = st.session_state.user_info.get("role", "user") if st.session_state.user_info else "user"
        email = st.session_state.user_info.get("email", "") if st.session_state.user_info else ""
        st.success(f"Signed in as: **{email}**")
        st.caption(f"Role: `{role.upper()}`")

        if st.button("Log Out", use_container_width=True):
            try:
                requests.post(
                    f"{st.session_state.api_url}/auth/logout",
                    headers=get_auth_headers(),
                    timeout=5,
                )
            except Exception:
                pass
            st.session_state.token = None
            st.session_state.user_info = None
            st.session_state.conversation_id = None
            st.session_state.messages = []
            st.rerun()
    else:
        auth_mode = st.radio("Account Action", ["Sign In", "Create Account"], horizontal=True)

        if auth_mode == "Sign In":
            with st.form("login_form"):
                login_email = st.text_input("Email", value="aarav.patel@example.com")
                login_pass = st.text_input("Password", type="password", value="SecurePassword123!")
                submit_login = st.form_submit_button("Sign In", use_container_width=True)

                if submit_login:
                    try:
                        res = requests.post(
                            f"{st.session_state.api_url}/auth/login",
                            json={"email": login_email, "password": login_pass},
                            timeout=8,
                        )
                        if res.status_code == 200:
                            data = res.json()
                            st.session_state.token = data["access_token"]
                            # Fetch user profile
                            user_res = requests.get(
                                f"{st.session_state.api_url}/users/me",
                                headers={"Authorization": f"Bearer {data['access_token']}"},
                                timeout=5,
                            )
                            if user_res.status_code == 200:
                                st.session_state.user_info = user_res.json()
                            st.success("Successfully logged in!")
                            st.rerun()
                        else:
                            st.error(res.json().get("detail", "Authentication failed."))
                    except Exception as exc:
                        st.error(f"Connection error: {str(exc)}")

        else:
            with st.form("register_form"):
                reg_name = st.text_input("Full Name", value="Test User")
                reg_email = st.text_input("Email", value="user@example.com")
                reg_pass = st.text_input("Password", type="password", value="SecurePassword123!")
                submit_reg = st.form_submit_button("Register", use_container_width=True)

                if submit_reg:
                    try:
                        res = requests.post(
                            f"{st.session_state.api_url}/auth/register",
                            json={"full_name": reg_name, "email": reg_email, "password": reg_pass},
                            timeout=8,
                        )
                        if res.status_code == 201:
                            st.success("Account created successfully! Please sign in.")
                        else:
                            st.error(res.json().get("detail", "Registration failed."))
                    except Exception as exc:
                        st.error(f"Connection error: {str(exc)}")

    st.divider()
    st.markdown("### 📌 Features")
    st.markdown("- **Deterministic Intent Routing** (`weather`, `rag`, `both`, `neither`, `clarification`)")
    st.markdown("- **Open-Meteo Integration** (live metrics, 16-day forecasts, geocoding)")
    st.markdown("- **NDMA RAG Guidelines** (pgvector embeddings, citation tracking)")
    st.markdown("- **Zero-Hallucination Guardrails** & Alert Disclaimers")


# ---------------------------------------------------------
# Main App Layout: Tabs
# ---------------------------------------------------------
tab_chat, tab_weather, tab_eval, tab_docs = st.tabs([
    "💬 Assistant Chat",
    "🗺️ Live Weather Explorer",
    "📊 Benchmark Evaluation",
    "📚 Disaster Knowledge Base",
])

# ---------------------------------------------------------
# Tab 1: Assistant Chat
# ---------------------------------------------------------
with tab_chat:
    col_head1, col_head2 = st.columns([4, 1])
    with col_head1:
        st.subheader("Weather & Disaster Intelligence Assistant")
        st.caption("Ask questions about real-time weather forecasts, meteorological conditions, or disaster safety protocols.")
    with col_head2:
        if st.button("➕ New Conversation", use_container_width=True):
            st.session_state.conversation_id = None
            st.session_state.messages = []
            st.rerun()

    if not st.session_state.token:
        st.info("💡 Please sign in or create an account in the sidebar to interact with the assistant.")
    else:
        # Display conversation messages
        for idx, msg in enumerate(st.session_state.messages):
            role = msg["role"]
            content = msg["content"]
            with st.chat_message(role):
                st.markdown(content)

                if role == "assistant" and "metadata" in msg:
                    meta = msg["metadata"]
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Route", meta.get("routing_decision", "N/A").upper())
                    c2.metric("Confidence", meta.get("confidence", "N/A").upper())
                    c3.metric("Latency", f"{meta.get('latency_ms', 0)} ms")
                    if meta.get("location"):
                        c4.metric("Location", meta.get("location"))

                    # Sources expander
                    weather_srcs = meta.get("weather_sources", [])
                    doc_srcs = meta.get("document_sources", [])
                    if weather_srcs or doc_srcs:
                        with st.expander("🔎 Verified Citations & Provenance Data"):
                            if weather_srcs:
                                st.markdown("**Live Meteorological Sources:**")
                                for ws in weather_srcs:
                                    st.markdown(f"- **{ws.get('provider')}** | City: `{ws.get('city')}` | Observed: `{ws.get('retrieved_at')}` | Endpoint: `{ws.get('endpoint')}`")
                            if doc_srcs:
                                st.markdown("**Official Disaster Knowledge Documents:**")
                                for ds in doc_srcs:
                                    score = f" (Score: {ds.get('similarity_score'):.2f})" if ds.get('similarity_score') else ""
                                    st.markdown(f"- **[{ds.get('title')}]({ds.get('source_url')})** | Category: `{ds.get('category')}`{score}")

                    # Feedback section
                    msg_id = meta.get("message_id")
                    if msg_id:
                        with st.expander(f"⭐ Leave Feedback for Turn #{idx + 1}"):
                            with st.form(f"feedback_form_{msg_id}"):
                                rating = st.slider("Rating (1 = Poor, 5 = Excellent)", 1, 5, 5)
                                comment = st.text_input("Comments (optional)", max_chars=500)
                                submit_fb = st.form_submit_button("Submit Feedback")
                                if submit_fb:
                                    fb_res = requests.post(
                                        f"{st.session_state.api_url}/feedback/",
                                        headers=get_auth_headers(),
                                        json={"message_id": msg_id, "rating": rating, "comment": comment},
                                        timeout=5,
                                    )
                                    if fb_res.status_code == 201:
                                        st.success("Thank you for your feedback!")
                                    else:
                                        st.error(fb_res.json().get("detail", "Failed to submit feedback."))

        # Chat input box
        user_query = st.chat_input("Ask a weather or safety question (e.g. 'What is the temperature in Delhi?' or 'What is a heatwave?')")
        if user_query:
            # Append user message
            st.session_state.messages.append({"role": "user", "content": user_query})

            payload = {
                "message": user_query,
                "conversation_id": st.session_state.conversation_id,
            }

            with st.spinner("Analyzing intent, consulting meteorological sources & disaster knowledge base..."):
                try:
                    chat_res = requests.post(
                        f"{st.session_state.api_url}/chat/ask",
                        headers=get_auth_headers(),
                        json=payload,
                        timeout=35,
                    )
                    if chat_res.status_code == 200:
                        data = chat_res.json()
                        st.session_state.conversation_id = data.get("conversation_id")
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": data.get("answer", ""),
                            "metadata": data,
                        })
                        st.rerun()
                    else:
                        err_text = chat_res.json().get("detail", f"Server error ({chat_res.status_code})")
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"⚠️ **Error:** {err_text}",
                        })
                        st.rerun()
                except Exception as exc:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"⚠️ **Connection Error:** Could not contact backend: {str(exc)}",
                    })
                    st.rerun()


# ---------------------------------------------------------
# Tab 2: Live Weather Explorer
# ---------------------------------------------------------
with tab_weather:
    st.subheader("Live Open-Meteo Meteorological Explorer")
    st.caption("Inspect live observations, hourly forecasts, and extended 16-day daily forecast models.")

    if not st.session_state.token:
        st.info("💡 Please sign in to query live meteorological data.")
    else:
        col_w1, col_w2, col_w3 = st.columns([3, 1, 1])
        with col_w1:
            city_query = st.text_input("Target City / Municipality", value="Delhi")
        with col_w2:
            forecast_type = st.selectbox("Query Mode", ["Current Conditions", "Hourly (24h)", "Daily Forecast (1-16d)"])
        with col_w3:
            days_input = st.number_input("Forecast Days", min_value=1, max_value=16, value=5)

        if st.button("Fetch Live Weather", use_container_width=True):
            with st.spinner(f"Contacting Open-Meteo geocoding and forecast models for {city_query}..."):
                try:
                    if forecast_type == "Current Conditions":
                        endpoint = f"{st.session_state.api_url}/weather/current?city={city_query}"
                    elif forecast_type == "Hourly (24h)":
                        endpoint = f"{st.session_state.api_url}/weather/hourly?city={city_query}&hours=24"
                    else:
                        endpoint = f"{st.session_state.api_url}/weather/daily?city={city_query}&days={days_input}"

                    res = requests.get(endpoint, headers=get_auth_headers(), timeout=10)
                    if res.status_code == 200:
                        wdata = res.json()
                        st.success(f"Weather data retrieved for **{city_query}** (Latency: {wdata.get('latency_ms', 0)}ms)")

                        loc = wdata.get("location", {})
                        st.caption(f"Coordinates: `{loc.get('latitude')}, {loc.get('longitude')}` | Region: `{loc.get('region')}, {loc.get('country')}` | Timezone: `{loc.get('timezone')}`")

                        if forecast_type == "Current Conditions":
                            m1, m2, m3, m4, m5 = st.columns(5)
                            m1.metric("Temperature", f"{wdata.get('temperature_c')} °C")
                            m2.metric("Condition", wdata.get("weather_condition"))
                            m3.metric("Humidity", f"{wdata.get('humidity_percent')}%")
                            m4.metric("Wind Speed", f"{wdata.get('wind_speed_kmh')} km/h")
                            m5.metric("Rain Probability", f"{wdata.get('rain_probability_percent')}%")

                        elif forecast_type == "Daily Forecast (1-16d)":
                            daily_items = wdata.get("forecast_days", [])
                            if daily_items:
                                st.dataframe(daily_items, use_container_width=True)

                        elif forecast_type == "Hourly (24h)":
                            hourly_items = wdata.get("hourly_forecast", [])
                            if hourly_items:
                                st.dataframe(hourly_items, use_container_width=True)

                        with st.expander("Raw API JSON Payload"):
                            st.json(wdata)

                    else:
                        st.error(res.json().get("detail", f"Weather request failed ({res.status_code})"))
                except Exception as exc:
                    st.error(f"Error querying weather API: {str(exc)}")


# ---------------------------------------------------------
# Tab 3: Benchmark Evaluation
# ---------------------------------------------------------
with tab_eval:
    st.subheader("Official Benchmark Evaluation Dashboard")
    st.caption("Executes the 15 official assignment test cases through the production pipeline and computes deterministic metrics.")

    role = st.session_state.user_info.get("role") if st.session_state.user_info else None
    if role not in {"admin", "evaluator"}:
        st.warning("🔒 Running evaluation benchmarks is restricted to users with `EVALUATOR` or `ADMIN` roles.")
        st.info("You can sign in using evaluator credentials or register an evaluator account.")
    else:
        col_run1, col_run2 = st.columns([3, 1])
        with col_run1:
            st.markdown("Click below to run the end-to-end benchmark across all 15 official test questions.")
        with col_run2:
            run_btn = st.button("🚀 Run Evaluation Benchmark", use_container_width=True, type="primary")

        if run_btn:
            with st.spinner("Executing 15 benchmark test cases against production pipeline..."):
                try:
                    res = requests.post(
                        f"{st.session_state.api_url}/evaluation/run",
                        headers=get_auth_headers(),
                        timeout=90,
                    )
                    if res.status_code == 200:
                        st.success("Benchmark completed and recorded in database!")
                        bench_data = res.json()
                        st.session_state.last_bench = bench_data
                    else:
                        st.error(res.json().get("detail", "Benchmark execution failed."))
                except Exception as exc:
                    st.error(f"Error executing benchmark: {str(exc)}")

        # Fetch recent evaluation results
        try:
            hist_res = requests.get(
                f"{st.session_state.api_url}/evaluation/results?limit=50",
                headers=get_auth_headers(),
                timeout=10,
            )
            if hist_res.status_code == 200:
                results_data = hist_res.json()
                items = results_data.get("items", [])
                st.write(f"### Historical Benchmark Records ({results_data.get('total', 0)} total entries)")

                if items:
                    st.dataframe(items, use_container_width=True)
                else:
                    st.info("No benchmark results recorded yet. Click 'Run Evaluation Benchmark' above.")
        except Exception as exc:
            st.error(f"Could not load evaluation records: {str(exc)}")


# ---------------------------------------------------------
# Tab 4: Knowledge Base Documents
# ---------------------------------------------------------
with tab_docs:
    st.subheader("Disaster Advisory & Weather Safety Knowledge Base")
    st.caption("Documents ingested into pgvector with 384-dimensional embeddings (sentence-transformers/all-MiniLM-L6-v2).")

    st.markdown("### 📑 Official Ingested Guidelines")
    doc_catalog = [
        {"Title": "IMD Heatwave Safety Guide & Action Plan", "Category": "heatwave", "Source": "https://mausam.imd.gov.in/heatwave-guide", "Chunks": 7},
        {"Title": "NDMA Flash Flood & Urban Drainage Safety", "Category": "rain_flood", "Source": "https://ndma.gov.in/flash-flood-handbook", "Chunks": 6},
        {"Title": "IMD Color-Coded Warning Protocols", "Category": "alerts", "Source": "https://mausam.imd.gov.in/color-codes", "Chunks": 6},
        {"Title": "Severe Thunderstorm & Lightning Safety (30-30 Rule)", "Category": "rain_flood", "Source": "https://ndma.gov.in/thunderstorm-protocol", "Chunks": 6},
        {"Title": "Extreme Cold Wave & Frost Advisory", "Category": "cold_wave", "Source": "https://ndma.gov.in/cold-wave-handbook", "Chunks": 6},
        {"Title": "NOAA & IMD Tropical Cyclone Classification", "Category": "tropical_storms", "Source": "https://www.nhc.noaa.gov/climo/cyclone-faq", "Chunks": 7},
        {"Title": "Manali High-Altitude Mountain Hiking Protocol", "Category": "hiking_safety", "Source": "https://ndma.gov.in/manali-mountain-safety", "Chunks": 8},
    ]
    st.table(doc_catalog)
