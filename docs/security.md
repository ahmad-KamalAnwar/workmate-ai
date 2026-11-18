# Security and permission model

Rules for day-to-day coding live in `.claude/rules/security.md`; this document describes the design.

## 1. Trust boundaries

| Zone | Trust | Examples |
|---|---|---|
| Authenticated user input | Validated, intent-bearing | Chat messages, settings, approvals |
| Model output | **Untrusted** | Plans, tool-call requests, drafted text |
| External content | **Untrusted** | Slack/Chat messages, emails, web pages, repo content, build logs |
| Backend services | Trusted | Permission engine, tool registry, scheduler |

Untrusted content can influence *what is proposed* but never *what is permitted*.

## 2. Authentication

- Email + password, argon2id hashing; login rate-limited.
- Server-side sessions: random 256-bit token in an httpOnly, `SameSite=Lax`, `Secure` (when HTTPS) cookie; only its hash is stored. Idle and absolute expiry. Logout revokes the row.
- CSRF: same-origin requests via Next.js rewrite + `SameSite` cookie; state-changing endpoints also require a custom header (`X-Requested-With`) or a double-submit token.
- First user is created via a CLI command (no open registration on a personal deployment).

## 3. Authorization and the permission engine

One function decides every tool execution:

```
decide(user, tool, input, context) -> Allow | RequireApproval(reason) | Deny(reason)
```

Inputs: the tool's declared `risk_level` (`read`, `write`, `sensitive`, `destructive`) and required scopes, the user's `permission_grants`, connected-account scopes, and context (scheduled vs interactive, task origin).

Defaults:

| Risk | Default |
|---|---|
| `read` | Allow |
| `write` (routine, e.g. draft, DM to self) | Allow if granted, else approval |
| `sensitive` (messages to others, email send, calendar invites, PR creation, build trigger) | Approval unless the user granted a standing permission |
| `destructive` / irreversible / financial / production | Always approval; standing grants not allowed |

The tool registry is the only path to integrations and calls `decide` itself; agents cannot obtain integration clients. Approvals bind to the exact tool input (hash) and expire.

## 4. Credentials and secrets

- OAuth tokens and user API keys encrypted with MultiFernet; key from `ENCRYPTION_KEYS` env (comma-separated, newest first) for rotation; `key_version` stored per row.
- Tokens are never returned by the API, never sent to models, never logged. A logging filter redacts known secret fields and token patterns.
- Minimum OAuth scopes per feature; incremental consent where the provider supports it. OAuth uses `state` + PKCE.
- `.env` is git-ignored; `.env.example` documents variables with placeholders.

## 5. Prompt-injection defenses

- External content is wrapped in clearly delimited, labeled blocks and the system prompt states it is data, not instructions.
- Tool selection is constrained to the tools an agent is registered for; model-proposed arguments are schema-validated.
- Sensitive actions resulting from content the user did not write (e.g. "reply to this email as instructed in it") require approval, showing the exact action.
- Recipients/targets of outbound messages are resolved against known mappings; new external recipients trigger approval.
- No tool gives models shell, filesystem, SQL, or arbitrary HTTP access.

## 6. Audit and idempotency

- `audit_log` records logins, settings changes, connections, approvals, and every external action (tool, target, result, idempotency key). Append-only.
- External actions use unique idempotency keys in `tool_executions`; outcomes that cannot be confirmed are marked `unknown` and not retried automatically.
- API acceptance is reported as "accepted", not "delivered", unless the provider confirms delivery.

## 7. Data isolation

Every repository method requires `user_id`; tests assert cross-user access returns 404.
