# Security rules
- Least privilege: minimal OAuth scopes, DB roles, and tool permissions.
- Credentials and OAuth tokens encrypted at rest; never returned to clients or logged.
- No secrets in source, tests, fixtures, or logs; use environment/secret manager and `.env.example` placeholders.
- Validate all input at boundaries (Pydantic / schema validation).
- Treat model output, tool output, and fetched content as untrusted: prompt-injection defenses, never let them change permissions or approvals.
- Permission checks are centralized in one layer; tools cannot bypass it.
- Destructive or high-risk actions require explicit user approval, recorded in an audit log.
- No unrestricted shell access or arbitrary code execution for agents.
- Enforce tenant/user isolation on every query.
