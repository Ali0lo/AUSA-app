# ==========================================
# FastAPI backend, and the seed job that fills its database.
#
# The build context is the REPOSITORY ROOT, not backend/. Every script resolves the
# repo root as `Path(__file__).parents[2]` and the prediction service as `parents[4]`,
# so data/ and models/ must sit beside backend/ in the image exactly as they do on
# disk. Building from backend/ alone puts DATA_PATH at /data and the Azerbaijan
# section reports itself absent.
# ==========================================
# 3.12, because constraints-tested.txt records the versions installed for the Python
# 3.12 release checks. On 3.11 its numpy==2.5.3 pin has no distribution and pip cannot
# resolve. Matching it also gives the image scikit-learn 1.9.1 -- the version
# models/metrics.json names -- so the model the seed service trains and the metrics
# beside it agree on more than the timestamp.
FROM python:3.12-slim

# /app is the repo root inside the image; the application runs from /app/backend.
WORKDIR /app/backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend

# gcc and libpq-dev build asyncpg and psycopg2; curl serves the healthcheck.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Dependencies first, so editing application code does not reinstall them.
COPY backend/requirements.txt backend/constraints-tested.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt -c constraints-tested.txt

COPY backend/ /app/backend/

# The curated catalogue, the DP catalogue and the DİM cutoff history. The seed
# service loads these into PostgreSQL and trains the Azerbaijan model from them.
COPY data/ /app/data/

# metrics.json only; the .joblib is built by the seed service into this directory.
COPY models/ /app/models/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
