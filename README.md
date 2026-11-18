# workmate-ai

Personal autonomous AI work assistant. See [docs/architecture.md](docs/architecture.md) and the progress checklist in [docs/roadmap.md](docs/roadmap.md).

## Quickstart (local)

Requires Docker with Compose v2.

```bash
cp .env.example .env          # set POSTGRES_PASSWORD
docker compose up -d --build
curl http://127.0.0.1:8000/health/ready
```
