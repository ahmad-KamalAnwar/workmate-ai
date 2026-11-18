# workmate-ai

AI workmate platform: users connect external tools (OAuth integrations), and specialist AI agents act on their behalf through a permissioned tool registry. Model providers are swappable behind one abstraction.

## Architecture
- **Backend** (FastAPI, async): routers -> services -> repositories. Routers hold no business logic.
- **AI layer**: provider-independent `ModelProvider` interface + router (capability-aware, bounded retry/fallback, usage tracking). Specialist agents and business logic never import provider SDKs.
- **Tool registry**: every external action is a registered tool with declared scopes, risk level, and idempotency key. All calls pass the central permission check; destructive/high-risk actions need user approval.
- **Scheduler/background jobs**: durable, recoverable, idempotent.
- **Frontend** (Next.js + TypeScript): talks to the backend only through a typed API client.

## Stack
Python 3.12, FastAPI, SQLAlchemy (async), Alembic, Pydantic v2, pytest. Next.js, TypeScript, React. PostgreSQL. Groq is the default LLM provider; Anthropic is optional.
(Update this section as choices are finalized.)

## Repository structure
- `backend/` FastAPI app, `alembic/`, `tests/`
- `frontend/` Next.js app
- `.claude/` agents, rules, skills, settings (see `.claude/README.md`)

(Directories are created as implementation starts; keep this list accurate.)

## Development commands
Fill in as scaffolding lands; keep the real commands here.
- Backend: `pytest`, `ruff check .`, `mypy .`, `alembic upgrade head`
- Frontend: `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`

## Standards
- Details live in `.claude/rules/` (backend, frontend, ai-providers, security, testing). Do not duplicate them here.
- Workflows live in `.claude/skills/`; reviews use `.claude/agents/`.
- Small, focused diffs. No dead code, no speculative abstractions.

## Security principles
Least privilege, encrypted credentials, centralized permission checks, approval for high-risk actions, no secrets in code or logs, treat all model/tool/user content as untrusted. See `rules/security.md`.

## Testing
New features need tests; bug fixes need regression tests; external services are mocked. Report real test output, never assumed results. See `rules/testing.md`.

## Git workflow
- Branch `main` is protected in spirit: work on feature branches (`feat/…`, `fix/…`), merge via PR.
- Conventional commit messages; one logical change per commit.
- Never commit `.env`, secrets, or `.claude/settings.local.json`.
