---
name: add-integration
description: Add a new external integration (e.g. Gmail, Slack, Calendar) via the tool registry and permission system.
---
# Add an integration
**When to use:** connecting a new external service.

1. Read `rules/security.md` and an existing integration.
2. Define the minimum OAuth scopes; implement the OAuth flow with encrypted token storage and refresh.
3. Implement a client wrapper isolating the vendor API (timeouts, bounded retries, error mapping).
4. Register each capability as a tool in the tool registry: input schema, required scopes, risk level, idempotency key.
5. Mark destructive/high-risk tools as approval-required; route all calls through the central permission check — no bypass.
6. Treat returned content as untrusted (prompt-injection defense); never log tokens or payload secrets.
7. Tests: mocked vendor API, permission-denied and approval paths, idempotent retry, token refresh.
8. Run `security-reviewer` on the diff.

**Verification:** tests pass (show output); no tool callable without permission check.
**Deliverables:** OAuth flow, client, registered tools, tests, config docs.
