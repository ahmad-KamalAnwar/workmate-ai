# Testing rules
- New features ship with tests; bug fixes ship with a regression test that fails before the fix.
- External integrations and model providers are mocked in tests; no live network calls.
- Provider adapters pass shared contract tests.
- Scheduler/background jobs have recovery tests (crash/restart, missed runs).
- Retried operations have idempotency tests (no duplicate side effects).
- Always run the tests and report the actual result; never claim a pass you did not observe. If tests cannot run, say so.
