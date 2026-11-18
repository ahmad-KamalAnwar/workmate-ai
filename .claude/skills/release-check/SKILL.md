---
name: release-check
description: Pre-release verification of tests, migrations, configuration, secrets, build output, and documentation.
---
# Release check
**When to use:** before tagging or deploying.

1. Tests: run full backend and frontend suites; report actual results.
2. Lint/type checks pass.
3. Migrations: `alembic upgrade head` on a clean DB and from the previous release; single head; downgrade sanity where applicable.
4. Configuration: all required env vars documented in `.env.example`; no dev defaults in production config.
5. Secrets: scan the repo and diff; confirm `.env` and `settings.local.json` untracked.
6. Build: `npm run build` and backend start succeed; inspect output for warnings.
7. Docs: README, CLAUDE.md, and changelog reflect changes.
8. Run the `security-audit` skill for security-relevant releases.

**Verification:** paste real command results; any skipped step is stated explicitly.
**Deliverables:** go/no-go report with blockers listed.
