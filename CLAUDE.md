# workmate-ai

WorkMate AI: a personal autonomous work assistant (web app). It takes natural-language instructions, plans tasks, acts in external apps through permissioned tools, runs scheduled/recurring work, and keeps persistent memory. Locally hosted via Docker Compose.

## Architecture
Modular monolith — see `docs/architecture.md` (components, flows, decisions D1–D9).
- **Backend** (FastAPI, async): routers -> services -> repositories. Routers hold no business logic.
- **AI gateway** (`docs/ai-gateway.md`): provider-independent interface, Groq default, Anthropic optional, routing modes groq_only / anthropic_only / smart (default). Orchestrator and agents never import provider SDKs.
- **Tools + permission engine** (`docs/security.md`): every external action is a registered tool with risk level and idempotency key; one central permission decision; high-risk actions need approval.
- **Scheduler**: Postgres-backed persistent jobs dispatched to Celery; restart-safe and idempotent; default timezone Asia/Karachi.
- **Frontend** (Next.js): talks to the backend only through the typed API client.

## Stack
Python 3.12, FastAPI, SQLAlchemy 2 (async), Alembic, Pydantic v2, Celery + Redis, PostgreSQL (pgvector later), pytest. Next.js, TypeScript, Tailwind CSS. Docker Compose.

## Repository structure
- `backend/` FastAPI app (`app/<module>/`), `alembic/`, `tests/`
- `frontend/` Next.js app
- `docs/` architecture, database, ai-gateway, security, roadmap
- `.claude/` agents, rules, skills, settings (see `.claude/README.md`)

Modules are added in the phase that needs them; keep this list accurate.

## Progress
`docs/roadmap.md` is the implementation checklist. Work phase by phase; tick items only after verification; update it in the same change.

## Development commands
Everything runs in Docker (host Python/Node are too old). First time: `cp .env.example .env` and set a password.
- Start / stop: `docker compose up -d --build` / `docker compose down`
- Health: `http://127.0.0.1:8000/health/ready` (API docs at `/docs`)
- Backend checks: `docker compose exec api sh -c "pytest -q && ruff check . && ruff format --check . && mypy app tests"`
- Unit tests only: `docker compose exec api pytest -q -m "not integration"`
- Logs: `docker compose logs -f api worker`
- After changing backend dependencies: `docker compose run --rm api uv lock`, then rebuild.
- Frontend: added later in Phase 1.

## Standards
- Details live in `.claude/rules/` (backend, frontend, ai-providers, security, testing). Do not duplicate them here.
- Workflows live in `.claude/skills/`; reviews use `.claude/agents/`.
- Small, focused diffs. No dead code, no speculative abstractions, no unnecessary dependencies.
- When a technical decision is uncertain, present alternatives with a recommendation before implementing.

## Security principles
Least privilege, encrypted credentials, centralized permission checks, approval for high-risk actions, no secrets in code or logs, treat all model output and external content as untrusted. See `rules/security.md`.

## Testing
New features need tests; bug fixes need regression tests; external services are mocked. Report real test output, never assumed results. See `rules/testing.md`.

## Git workflow
- Never push directly to `main`: work on feature branches (`feat/…`, `fix/…`, `docs/…`), merge via reviewed PR.
- Conventional commit messages; one logical change per commit.
- Never commit `.env`, secrets, or `.claude/settings.local.json`.
