# Database design

PostgreSQL, managed through Alembic migrations. All IDs are UUIDv4 (`id uuid pk`), all timestamps are `timestamptz` in UTC. Every user-owned row has `user_id` and every query filters by it. Columns marked 🔒 are encrypted at the application layer (see [security.md](security.md)).

Phase column = when the table is introduced.

## Identity and settings

| Table | Key columns | Phase |
|---|---|---|
| `users` | email (unique, citext), password_hash, display_name, timezone (default `Asia/Karachi`), is_active, created_at | 1 |
| `sessions` | user_id, token_hash (unique), expires_at, last_seen_at, user_agent, ip | 1 |
| `user_settings` | user_id (pk), routing_mode (`groq_only`/`anthropic_only`/`smart`, default `smart`), preferences jsonb | 2 |
| `provider_credentials` | user_id, provider, api_key 🔒, key_version, status, last_checked_at; unique(user_id, provider). Env keys are the default; this table holds user-supplied overrides | 2 |

## Conversations and tasks

| Table | Key columns | Phase |
|---|---|---|
| `conversations` | user_id, title, created_at, archived_at | 2 |
| `messages` | conversation_id, role (`user`/`assistant`/`system`/`tool`), content, task_id?, ai_call_id?, created_at | 2 |
| `tasks` | user_id, conversation_id?, source (`chat`/`schedule`), title, status (`pending`/`planning`/`running`/`awaiting_approval`/`succeeded`/`failed`/`cancelled`), plan jsonb, error, created_at, started_at, finished_at | 1 (minimal), 3 (full) |
| `task_steps` | task_id, seq, kind (`model`/`tool`), agent, tool_name?, input jsonb, output jsonb, status, error, started_at, finished_at | 3 |

## AI usage

| Table | Key columns | Phase |
|---|---|---|
| `ai_calls` | user_id, task_id?, purpose, provider, model, routing_reason, attempt, fallback_from?, status, input_tokens, output_tokens, latency_ms, cost_estimate, error_code, created_at | 2 |

## Tools, permissions, audit

| Table | Key columns | Phase |
|---|---|---|
| `tool_executions` | user_id, task_step_id?, tool_name, idempotency_key (**unique**), input jsonb, status (`pending`/`succeeded`/`failed`/`unknown`), result jsonb, external_ref, created_at, finished_at | 3 |
| `permission_grants` | user_id, tool_name or pattern, effect (`allow`/`require_approval`/`deny`), conditions jsonb | 3 |
| `approvals` | user_id, task_step_id, tool_name, input_summary, risk_level, status (`pending`/`approved`/`denied`/`expired`), decided_at, expires_at | 3 |
| `audit_log` | user_id?, actor (`user`/`agent`/`system`), action, target, details jsonb, created_at. Append-only (no UPDATE/DELETE grants) | 1 |

`tool_executions.status = unknown` covers calls whose outcome could not be confirmed (e.g. network timeout after send). These are never auto-retried; they are reconciled or surfaced to the user.

## Integrations

| Table | Key columns | Phase |
|---|---|---|
| `integration_connections` | user_id, provider (`slack`/`google`/`github`/`jenkins`), account_ref, scopes text[], access_token 🔒, refresh_token 🔒, expires_at, key_version, status, created_at; unique(user_id, provider, account_ref) | 4 |
| `oauth_states` | state_hash, user_id, provider, pkce_verifier 🔒, expires_at | 4 |
| `external_mappings` | user_id, provider, kind (`user`/`channel`/`space`/`repo`…), external_id, display_name, metadata jsonb | 4 |

## Scheduler

| Table | Key columns | Phase |
|---|---|---|
| `scheduled_jobs` | user_id, task_template jsonb, schedule_type (`once`/`cron`), run_at?, cron_expr?, timezone, next_run_at (indexed), enabled, max_retries, created_at, cancelled_at | 5 |
| `job_runs` | job_id, scheduled_for, idempotency_key (**unique** = `job_id:scheduled_for`), task_id?, status, attempt, error, started_at, finished_at | 5 |

## Memory

| Table | Key columns | Phase |
|---|---|---|
| `memories` | user_id, kind (`fact`/`preference`/`mapping`/`note`), key, content, source (task/message id), confidence, created_at, updated_at, expires_at? | 3 |
| `memory_embeddings` | memory_id, model, embedding vector(n) | 8 |

## Indexes and constraints (beyond PKs/FKs)

- `sessions(token_hash)` unique, `sessions(user_id)`, `tasks(user_id, created_at)`, `audit_log(user_id, created_at)`; `messages(conversation_id, created_at)` in Phase 2
- `scheduled_jobs(next_run_at) WHERE enabled AND cancelled_at IS NULL`
- unique `tool_executions(idempotency_key)`, unique `job_runs(idempotency_key)`
- `ai_calls(user_id, created_at)` for usage dashboards
