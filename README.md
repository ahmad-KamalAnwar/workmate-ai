# workmate-ai

Personal autonomous AI work assistant. See [docs/architecture.md](docs/architecture.md) and the progress checklist in [docs/roadmap.md](docs/roadmap.md).

## Quickstart (local)

Requires Docker with Compose v2.

```bash
cp .env.example .env          # set POSTGRES_PASSWORD
docker compose up -d --build
docker compose exec api python -m app.auth.cli create-user --email you@example.com
```

Open http://127.0.0.1:3000 and sign in. API docs: http://127.0.0.1:8000/docs
