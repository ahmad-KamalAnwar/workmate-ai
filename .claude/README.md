# .claude configuration

Project-level Claude Code setup. Root `CLAUDE.md` holds the overview; everything detailed lives here.

- `agents/` – focused reviewers/implementers: architect, backend-engineer, frontend-engineer, security-reviewer, code-reviewer.
- `rules/` – standing constraints: backend (path-scoped), frontend (path-scoped), ai-providers, security, testing.
- `skills/` – procedures: implement-feature, add-ai-provider, add-integration, debug-issue, review-code, security-audit, release-check.
- `settings.json` – conservative shared permissions (no blanket Bash, destructive commands and `.env` reads denied). Personal overrides go in `settings.local.json` (git-ignored). No hooks yet; add only if deterministic and tested.

## Maintenance
When architecture, commands, or conventions change, update the relevant rule/skill and CLAUDE.md in the same change. Remove obsolete or duplicated instructions; keep files short.
