---
paths:
  - "backend/**"
---
# Backend rules
- Type hints on all functions; `mypy` clean.
- Pydantic models validate all request/response and external payloads.
- Layering: router -> service -> repository. No business logic in routers, no HTTP concerns in services.
- Dependencies (DB session, settings, clients) injected via FastAPI `Depends`; no module-level singletons with hidden state.
- Async end to end; no blocking I/O in async paths.
- One transaction per unit of work, owned by the service layer; roll back on error; no partial commits.
- Schema changes only via Alembic migrations (reviewed, reversible where practical); never edit applied migrations.
- Unit tests for services; integration tests for endpoints and repositories.
