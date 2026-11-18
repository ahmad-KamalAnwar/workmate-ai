---
name: security-audit
description: Audit the application against the project's security requirements.
---
# Security audit
**When to use:** before release, after auth/integration/tool changes, or on request.

Delegate to `security-reviewer` and check each item in `rules/security.md`:
1. Least privilege: OAuth scopes, DB roles, tool permissions.
2. Credentials/tokens encrypted at rest; absent from responses and logs.
3. Secrets scan of source, history, fixtures (`git grep` for keys; check `.env` is ignored).
4. Input validation at every boundary.
5. Prompt-injection defenses; untrusted content cannot alter permissions.
6. Central permission check covers every tool; no bypass paths.
7. High-risk actions require approval and are audit-logged.
8. No unrestricted shell/code execution.
9. Tenant/user isolation on all queries; dependency vulnerability check.

**Verification:** cite evidence (file:line, command output) per item; mark unverified items.
**Deliverables:** findings by severity with fixes, plus a pass/fail checklist.
