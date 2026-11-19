# Roadmap and implementation checklist

Single source of progress across sessions. Tick items only when verified (tests/checks actually run). Each phase is developed on a feature branch and merged by PR.

Legend: `[x]` done and verified · `[ ]` open · `[~]` partially done (see note)

## Phase 0 — Architecture and Claude Code setup
- [x] Inspect repository (empty apart from README)
- [x] `CLAUDE.md` and `.claude/` (agents, rules, skills, settings) — verified loaded by Claude Code 2.1.327
- [x] Architecture document — [architecture.md](architecture.md)
- [x] Database design — [database.md](database.md)
- [x] AI provider design and routing — [ai-gateway.md](ai-gateway.md)
- [x] Security design — [security.md](security.md)
- [x] Repository structure (below)
- [x] Technical decisions D1–D9 approved (2026-11-19) ([architecture.md §5](architecture.md#5-technical-decisions))

## Phase 1 — Application foundation
- [x] Docker Compose: postgres (pgvector image), redis, migrate (one-shot), api, worker, frontend; health checks; ports bound to 127.0.0.1 (beat deferred to Phase 5)
- [x] `.env.example`; settings via pydantic-settings with validation
- [x] FastAPI app: structured JSON logging, `/health/live`, `/health/ready` (db + redis, timeouts, 503 when degraded)
- [x] Uniform API error envelope `{error: {code, message, details}}`
- [x] Async SQLAlchemy + Alembic; initial migration: users, sessions, audit_log, tasks (minimal); downgrade/upgrade exercised in tests; `alembic check` clean
- [x] Celery app wired to Redis with a ping task (verified round trip through the worker)
- [x] Auth: create-user CLI, login/logout/me, argon2id, server-side sessions (idle + absolute expiry), httpOnly SameSite cookie, CSRF header check, login throttling, audit entries
- [x] Tasks API: `GET /tasks` (per-user, newest first, bounded limit)
- [x] Next.js 15 (App Router, TS strict, Tailwind 4): login page, auth redirect, dashboard with service status and recent tasks (loading/empty/error states)
- [x] Typed API client from OpenAPI (`npm run gen:api`); `/api/*` rewrite to backend
- [x] Tests: backend 40 (unit + integration on a migrated test DB), frontend 15; ruff, mypy strict, eslint, tsc, `next build` all pass
- [x] CLAUDE.md commands and README quickstart updated

Known limitations (carried forward):
- Login throttling keys on client IP + email, but behind the Next.js proxy every request has the proxy's IP, so in practice it is per-email. Fine for single-user local use; revisit with trusted proxy headers in Phase 9.
- `audit_log` is append-only by convention; DB-level enforcement (separate role without UPDATE/DELETE) is a Phase 9 item.
- Conversations and messages tables moved to Phase 2, where the chat API uses them.

## Phase 2 — AI provider gateway
- [ ] Interface, error hierarchy, ChatRequest/Response types
- [ ] Groq adapter; Anthropic adapter (optional registration)
- [ ] Model config + capability validation; verified model IDs
- [ ] Routing modes: groq_only, anthropic_only, smart (default)
- [ ] Bounded retries, fallback, structured-output validation/repair
- [ ] `ai_calls` usage tracking; provider health endpoint
- [ ] Contract tests for adapters (mocked); routing/fallback tests; Groq-only test
- [ ] Basic conversational UI (milestone 1) and AI settings page
- [ ] Persistent task records for chat turns (milestone 1)

## Phase 3 — Core agent runtime
- [ ] Orchestrator: classify → plan → dispatch; task/step lifecycle
- [ ] Specialist agent registry
- [ ] Tool registry with typed I/O, risk levels, idempotency
- [ ] Permission engine, approvals API + UI
- [ ] Initial structured memory
- [ ] Import-linter boundary contracts
- [ ] Tests: permission decisions, approval resume, idempotent tool execution

## Phase 4 — Communication integrations
- [ ] OAuth framework (state + PKCE, encrypted tokens, refresh)
- [ ] Slack: connect, workspace/user/channel discovery, read, DM, channel post, schedule, cancel
- [ ] Google Chat: user-OAuth vs Chat-app auth decision, spaces, DM, space messaging, read, scheduled send, cancel
- [ ] Results reported as accepted vs confirmed

## Phase 5 — Scheduler and automation
- [ ] scheduled_jobs/job_runs, dispatcher, tz-aware once + cron (default Asia/Karachi)
- [ ] Cancellation, retry policy, restart recovery, idempotency
- [ ] Failure notifications, execution history UI
- [ ] Tests: survives restart, no double execution, cancellation, recurrence

## Phase 6 — Email and calendar
- [ ] Gmail: read, search, summarize, draft, send (approval)
- [ ] Calendar: read, create, update, delete (confirm), availability, reminders

## Phase 7 — Developer integrations
- [ ] GitHub: repos, commits/branches, PR summaries, issues, PR creation (approval), review assistance
- [ ] Jenkins: jobs, status, logs, trigger (approval), pipeline monitoring

## Phase 8 — Advanced memory and research
- [ ] pgvector embeddings, semantic retrieval
- [ ] Research workflows, reports, recurring research

## Phase 9 — Security, observability, production readiness
- [ ] Security audit (skill), token storage and encryption review, prompt-injection review
- [ ] Metrics and structured log review, backups and restore procedure
- [ ] Coverage improvements, resource review

## Repository structure (target)

```
workmate-ai/
├── CLAUDE.md
├── README.md
├── docker-compose.yml
├── .env.example
├── docs/                      architecture, database, ai-gateway, security, roadmap
├── backend/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── alembic/versions/
│   ├── app/
│   │   ├── main.py            app factory, routers
│   │   ├── core/              config, db, logging, crypto, errors
│   │   ├── auth/              models, schemas, service, router, deps
│   │   ├── conversations/
│   │   ├── tasks/
│   │   ├── audit/
│   │   ├── ai_gateway/        interface, providers/{groq,anthropic}.py, registry, routing, usage   (Phase 2)
│   │   ├── orchestrator/      (Phase 3)
│   │   ├── agents/            (Phase 3)
│   │   ├── tools/             (Phase 3)
│   │   ├── permissions/       (Phase 3)
│   │   ├── memory/            (Phase 3)
│   │   ├── integrations/      slack/, google/, github/, jenkins/   (Phase 4+)
│   │   ├── scheduler/         (Phase 5)
│   │   └── worker.py          Celery app
│   └── tests/{unit,integration}/
└── frontend/
    ├── package.json
    ├── Dockerfile
    └── src/
        ├── app/               routes: login, dashboard, chat, settings
        ├── components/
        └── lib/api/           typed client
```

Each module is a package with `models.py`, `schemas.py`, `repository.py`, `service.py`, `router.py` as needed; modules are created in the phase that needs them, not up front.
