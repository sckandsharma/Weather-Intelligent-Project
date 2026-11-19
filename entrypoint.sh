#!/usr/bin/env bash
set -e

echo "=== Weather Intelligence Assistant Startup ==="
if [ "$#" -gt 0 ]; then
    echo "Executing custom command: $@"
    exec "$@"
fi

echo "Running database migrations (Alembic)..."
alembic upgrade head

echo "Database migrations complete."
echo "Starting FastAPI Uvicorn Server on 0.0.0.0:8000..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
