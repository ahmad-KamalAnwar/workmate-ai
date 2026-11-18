---
name: review-code
description: Review the current diff or a PR for correctness, maintainability, performance, tests, and regressions.
---
# Review code
**When to use:** before merging or when asked for a review.

1. Obtain the real diff (`git diff main...HEAD` or `gh pr diff`); do not rely on summaries.
2. Delegate to the `code-reviewer` agent; add `security-reviewer` for auth, OAuth, tools, secrets, or prompt handling.
3. Check against `.claude/rules/`, test adequacy, migrations, and error handling.
4. Run relevant tests/lint and report real output.

**Verification:** every finding cites file:line.
**Deliverables:** ranked findings and a clear approve / request-changes verdict.
