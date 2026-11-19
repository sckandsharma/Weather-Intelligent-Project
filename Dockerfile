# syntax=docker/dockerfile:1
# Multi-stage Dockerfile for Weather Intelligence & Advisory Assistant

# -------------------------------------------------------------
# Stage 1: Builder
# -------------------------------------------------------------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

# Install system compilation dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies with resilient timeouts
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=120 --retries=5 --prefix=/install -r requirements.txt

# Pre-download SentenceTransformer embedding model at build time
# Prevents cold-start delays and runtime HuggingFace hub dependencies in production
RUN python3 -c "\
import sys;\
sys.path.insert(0, '/install/lib/python3.11/site-packages');\
from sentence_transformers import SentenceTransformer;\
SentenceTransformer('all-MiniLM-L6-v2')\
"

# -------------------------------------------------------------
# Stage 2: Runner (Minimal & Hardened)
# -------------------------------------------------------------
FROM python:3.11-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    HF_HOME=/home/appuser/.cache/huggingface

# Install runtime utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root application user
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -m -s /bin/bash appuser

WORKDIR /app

# Copy installed dependencies and pre-cached HuggingFace models from builder
COPY --from=builder /install /usr/local
COPY --from=builder /root/.cache/huggingface /home/appuser/.cache/huggingface

# Copy application code with proper ownership
COPY --chown=appuser:appgroup . /app

# Set correct permissions
RUN chmod +x /app/entrypoint.sh && \
    chown -R appuser:appgroup /home/appuser/.cache && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

EXPOSE 8000

# Container healthcheck hitting the public /health endpoint
HEALTHCHECK --interval=20s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
