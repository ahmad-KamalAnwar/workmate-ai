---
name: implement-feature
description: Implement a new feature end to end (design, code, tests, docs). Use when asked to build or extend functionality.
---
# Implement a feature
**When to use:** any new user-facing or internal capability.

1. Restate the goal and acceptance criteria; ask only if truly ambiguous.
2. For cross-cutting changes, consult the `architect` agent first.
3. Read relevant code and the applicable `.claude/rules/` files.
4. Implement in small steps: schema/migration -> repository -> service -> router -> frontend.
5. Write tests alongside (unit + integration; mocks for externals).
6. Run linters, type checks, and tests; fix failures.
7. Have `code-reviewer` (and `security-reviewer` if security-relevant) review the diff.
8. Update CLAUDE.md / rules / docs if commands or conventions changed.

**Verification:** real test, lint, and type-check output.
**Deliverables:** code, migration, tests, doc updates, short summary with verification results.
