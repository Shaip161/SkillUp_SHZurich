# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Repository layout

This repo holds two independent systems:

- `backend/` + `frontend/` — **Job Matcher** (the active product)
- `Agentic_learning/` — a separate agentic learning system that is **out of scope**; do not modify it

The Job Matcher exposes `POST /gap/{job_id}` as a contract endpoint that `Agentic_learning/` will consume independently.

---

## Common commands

All development runs inside Docker. There is no local Python/Node environment — `node_modules` and Python packages only exist inside containers.

```bash
# Start everything
docker-compose up

# Start just infrastructure (postgres + redis)
docker-compose up -d postgres redis

# Run database migrations
docker-compose run --rm backend alembic upgrade head

# Downgrade and re-run from scratch
docker-compose run --rm backend alembic downgrade base && docker-compose run --rm backend alembic upgrade head

# Run all backend tests
docker-compose run --rm backend pytest -v

# Run a single test file
docker-compose run --rm backend pytest tests/test_matcher.py -v

# Run a single test by name
docker-compose run --rm backend pytest tests/test_skill_extractor.py::test_parses_valid_json_response -v

# TypeScript type check (authoritative — IDE errors are false positives without local node_modules)
docker-compose run --rm frontend npx tsc --noEmit

# Trigger the ingestion pipeline manually
docker-compose run --rm backend python -c "
import asyncio
from tasks.ingest_jobs import _run_ingestion_async
asyncio.run(_run_ingestion_async())
"

# Check service health
curl http://localhost:8000/health
```

---

## Architecture

### Data flow

**Ingestion (Celery, runs daily at 02:00 UTC):**
```
Adzuna API → skill_extractor.py (Claude) → embedder.py (Gemini) → jobs table
```

**CV matching (request-time):**
```
POST /match → cv_parser.py → skill_extractor.py → embedder.py → matcher.search_jobs() → DB
```

**Gap analysis:**
```
POST /gap/{job_id} → jobs.required_skills − user_profiles.skills → JSON response
```
This endpoint is a pure data contract (no LLM calls). The agentic learning system consumes it directly.

### Backend (`backend/app/`)

- `config.py` — single `Settings` instance loaded from `.env` via pydantic-settings; imported everywhere
- `database.py` — async SQLAlchemy engine + `get_db` FastAPI dependency
- `models/` — ORM models and Pydantic schemas co-located in the same file per entity
- `services/` — stateless async functions; routes are thin orchestrators that call these
- `tasks/` — Celery tasks; each task calls `asyncio.run()` and creates its own engine with `NullPool` (required to avoid asyncpg event-loop conflicts)

### Frontend (`frontend/src/`)

- All pages are `'use client'` components; no server-side data fetching
- `user_id` and match results travel via `sessionStorage` (landing → matches) and URL query params (matches → job detail)
- `src/lib/api.ts` — all typed fetch wrappers; every component calls these, never `fetch` directly
- `src/lib/types.ts` — TypeScript interfaces that mirror backend Pydantic response schemas exactly

---

## Critical non-obvious constraints

### Embeddings
- Model: `models/gemini-embedding-001` (primary), `models/gemini-embedding-2` (fallback)
- Dimensions: **3072** — the DB schema (`vector(3072)`) and both `build_job_embedding_input` / `build_cv_embedding_input` must stay in sync
- `google.generativeai.embed_content` is synchronous; it is wrapped in `asyncio.to_thread` in `embedder.py`
- The embedding input format must be **identical** across jobs and CVs — changing one requires changing the other and re-embedding all existing records
- Jobs use `task_type="retrieval_document"`, CVs use `task_type="retrieval_query"`

### pgvector + asyncpg
- Do **not** use `:param::vector` in `text()` queries — asyncpg's `$N` substitution conflicts with `::` cast syntax and leaves the parameter unreplaced
- Workaround in `matcher.py`: embed the vector literal directly into the f-string SQL: `'{vector_literal}'::vector`

### Database
- Postgres host port is `5433` (not `5432`) to avoid conflicts with a local Postgres install
- Docker services connect to each other via `postgres:5432` (service name + container port)
- The `DATABASE_URL` in `.env` must use `@postgres:5432`, not `@localhost`
- No HNSW index — brute-force scan is used intentionally for demo-scale data

### Ingestion
- `MAX_JOBS_PER_CATEGORY=10` in `.env` caps ingestion for development; set to `0` to disable for production
- Celery tasks create their own `AsyncSession` with `NullPool` — they do **not** use the shared `AsyncSessionLocal` from `database.py`

### Skill normalisation
- Canonical skill names (`ReactJS→React`, `ML→Machine Learning`, etc.) are enforced by the LLM system prompt in `skill_extractor.py`, not by Python code
- The same extractor function and prompt handle both job postings and CVs

---

## Environment variables

Copy `.env.example` to `.env` and fill in:

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude (skill extraction) |
| `GEMINI_API_KEY` | Gemini (embeddings) |
| `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` | Job source API |
| `DATABASE_URL` | Must be `postgresql+asyncpg://postgres:postgres@postgres:5432/jobmatcher` inside Docker |
| `REDIS_URL` | `redis://redis:6379/0` inside Docker |
| `MAX_JOBS_PER_CATEGORY` | `10` for dev, `0` to disable cap |
