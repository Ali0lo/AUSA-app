# AUSA Backend Service (FastAPI + Async SQLAlchemy)

This directory contains the Python FastAPI backend, database models, async scrapers, RAG vector retrieval, and machine learning inference services.

---

## 🚀 Database Seeding & CLI Commands

### 1. Seed Database Fixtures
Populate baseline universities (ADA, UNEC, BHOS/BANM, TU Munich, RWTH Aachen, Heidelberg), scholarships (DAAD, Azerbaijani State Program, ADA Merit), and mock RAG vector embedding chunks:

```bash
# Execute from the backend directory
PYTHONPATH=. python -m scripts.seed_db
```

Or trigger database fixture population dynamically via the Admin API endpoint:
```bash
curl -X POST http://localhost:8000/api/v1/admin/seed \
     -H "Content-Type: application/json"
```

---

## 🔄 Database Migrations (Alembic)

```bash
# Generate a new migration script
alembic revision --autogenerate -m "Add new columns"

# Apply pending migrations to PostgreSQL
alembic upgrade head
```

---

## 🧪 Unit Testing

```bash
# Run pytest suite
PYTHONPATH=. pytest tests/
```

