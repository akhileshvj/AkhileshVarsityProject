# AkhileshVarsityProject

FastAPI service for AuraMatch AI.

## Run locally

```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`, with health checks at
`/api/v1/health` and `/api/v1/health/deep`.

## Run with Docker

```bash
docker compose -f docker/docker-compose.yml up --build
```

## Test

```bash
pytest
```