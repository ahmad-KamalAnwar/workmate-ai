# Architecture

WorkMate AI is a personal autonomous work assistant: a web app that takes natural-language instructions, plans tasks, calls external applications through permissioned tools, runs scheduled/recurring work, and keeps persistent memory.

It is a **modular monolith**: one FastAPI codebase with strict module boundaries, plus Celery workers running the same code. No microservices.

Related: [database.md](database.md) · [ai-gateway.md](ai-gateway.md) · [security.md](security.md) · [roadmap.md](roadmap.md)

## 1. Overview

```
 Browser
   │  HTTPS (same-origin via Next.js rewrite, session cookie)
   ▼
 Next.js (frontend) ──/api/*──▶ FastAPI (api)
                                  │
       ┌──────────────────────────┼─────────────────────────────┐
       │                          ▼                             │
       │   auth ── conversations ── orchestrator ── memory      │
       │                              │                         │
       │               ┌──────────────┼───────────────┐         │
       │               ▼              ▼               ▼         │
       │          ai_gateway     agents (specialists)  scheduler│
       │          (Groq,              │                   │     │
       │           Anthropic)         ▼                   │     │
       │                         tools (registry)         │     │
       │                              │                   │     │
       │                         permissions ◀── approvals│     │
       │                              │                   │     │
       │                         integrations (Slack, Google, GitHub, Jenkins…)
       └──────────────────────────────────────────────────┼─────┘
              │                                           │
          PostgreSQL ◀────────────── Celery worker / beat ◀── Redis (broker)
```

## 2. Component responsibilities

| Module | Owns | Must not |
|---|---|---|
| `core` | Settings, DB engine/session, logging, crypto, error types | Contain business logic |
| `auth` | Users, password hashing, sessions, current-user dependency | — |
| `conversations` | Conversations and messages, chat API | Call providers directly |
| `orchestrator` | Turn handling: classify → plan → dispatch to agents → track task lifecycle | Call provider SDKs or external APIs |
| `agents` | Specialist agents (comms, email, calendar, dev, research) declared via a registry | Call integrations except through tools |
| `ai_gateway` | Provider interface, adapters, registry, capabilities, routing, fallback, usage, health | Execute tools or side effects |
| `tools` | Tool registry, typed input/output schemas, execution with idempotency | Skip the permission engine |
| `permissions` | Single decision point: allow / deny / require approval; approval records | Be bypassable |
| `integrations` | One package per external service: OAuth, API client, error mapping | Be called by anything except tools/OAuth routes |
| `scheduler` | Persistent jobs, recurrence, dispatch to Celery, recovery, run history | Depend on the browser |
| `tasks` | Task and step records, status transitions, execution history | — |
| `memory` | Structured memory (facts, preferences, mappings); semantic retrieval later | Store secrets |
| `audit` | Append-only audit log | Be mutable |

Dependency direction (allowed imports point down):

```
api routers → services (conversations, orchestrator, scheduler, settings)
orchestrator → agents → tools → permissions, integrations
orchestrator/agents → ai_gateway
everything → core, tasks, audit
```

Enforced in Phase 3 by an import-linter contract (e.g. `agents`/`orchestrator` cannot import `groq` or `anthropic`; only `integrations` imports vendor API clients).

## 3. Key flows

**Chat turn:** `POST /conversations/{id}/messages` → store user message → orchestrator classifies via gateway (cheap Groq model) → simple reply, or a task with a plan → each step either generates text (gateway) or calls a tool (registry → permission check → integration) → results stored as task steps and messages → audit entries.

**Approval:** permission engine returns `requires_approval` → step paused (`awaiting_approval`) → UI shows an approval card → user approves/denies → step resumes with the **same** idempotency key.

**Scheduled job:** user creates a schedule (tz-aware) → row in `scheduled_jobs` → beat dispatcher claims due jobs (`FOR UPDATE SKIP LOCKED`) → creates a `job_run` with a deterministic idempotency key (`job_id:scheduled_for`) → Celery worker executes → result/failure recorded, notification on failure.

**Provider fallback:** gateway retries are confined to the model call. Tool calls happen *after* a model response is accepted and are keyed by idempotency key, so a timeout/retry/fallback cannot re-run an external action.

## 4. Deployment (local)

Docker Compose services: `frontend` (Next.js), `api` (FastAPI/uvicorn), `worker` (Celery worker), `beat` (Celery beat dispatcher), `postgres` (pgvector image, extension enabled only when needed), `redis`. Secrets via `.env` (git-ignored, `.env.example` committed).

## 5. Technical decisions

Status: **Proposed** until approved. Record changes here when a decision is made or revised.

| # | Decision | Recommendation | Alternatives |
|---|---|---|---|
| D1 | Dev runtime | Run everything in Docker Compose (Python 3.12, Node 22 images); host Python 3.10 / Node 18 are too old | Upgrade host toolchains |
| D2 | Python packaging | `uv` with `pyproject.toml` + lockfile | pip + requirements.txt; Poetry |
| D3 | Authentication | Email + password (argon2), server-side sessions in Postgres, httpOnly SameSite cookie; single-user use, multi-user-ready schema | JWT access/refresh tokens; OAuth login |
| D4 | DB access | SQLAlchemy 2 async + asyncpg in API; Celery tasks run async code via a per-task event loop | Sync SQLAlchemy everywhere; SQLModel |
| D5 | Scheduler | Postgres as source of truth (`scheduled_jobs`), Celery beat runs a 15 s dispatcher tick that claims due rows | celery-redbeat (state in Redis); APScheduler + SQL jobstore |
| D6 | AI gateway | Own thin adapters over the official `groq` and `anthropic` SDKs | LiteLLM (extra dependency, less control over capability checks) |
| D7 | Credential encryption | Fernet/MultiFernet (`cryptography`), key from env, versioned for rotation | DB-level pgcrypto; external KMS (later) |
| D8 | Frontend ↔ API | Next.js App Router; `/api/*` rewritten to FastAPI so cookies stay same-origin; typed client generated from OpenAPI | CORS with separate origins; tRPC |
| D9 | Semantic memory | pgvector deferred to Phase 8; image already includes it | Separate vector DB |
