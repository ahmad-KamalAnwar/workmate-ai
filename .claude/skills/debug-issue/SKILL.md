---
name: debug-issue
description: Systematically diagnose and fix a bug, ending with a regression test.
---
# Debug an issue
**When to use:** errors, failing tests, unexpected behavior.

1. Reproduce; capture the exact error, inputs, and environment.
2. Form hypotheses; gather evidence (logs, code paths, `git log` for recent changes) before changing code.
3. Identify the root cause, not just the symptom.
4. Write a failing regression test first.
5. Apply the minimal fix; confirm the test passes and the wider suite is unaffected.
6. Check for the same flaw elsewhere.

**Verification:** failing-then-passing test output.
**Deliverables:** fix, regression test, one-paragraph root-cause explanation.
