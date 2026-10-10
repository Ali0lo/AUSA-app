#!/bin/sh
set -e

echo "=== AUSA Backend Startup ==="

# Run database migrations and bootstrap catalogue data
if [ -n "$DATABASE_URL" ]; then
    echo "Running database bootstrap and migrations..."
    python -m scripts.bootstrap_catalogue || echo "Warning: Bootstrap finished with notice (continuing startup)."
fi

# Ensure Azerbaijan cutoff model is trained if missing
if [ ! -f /app/models/cutoff_coldstart_AZ.joblib ]; then
    echo "Training Azerbaijan cutoff coldstart model..."
    python -m scripts.train_cutoff_models --country AZ || echo "Notice: Cutoff model training skipped."
fi

# Index RAG documents if OPENAI_API_KEY is configured
if [ -n "$OPENAI_API_KEY" ]; then
    echo "Checking and indexing RAG university documents..."
    python -m scripts.index_documents --if-empty || echo "Notice: Document indexing skipped or completed."
fi

PORT="${PORT:-8000}"
echo "Launching Uvicorn on 0.0.0.0:${PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"

