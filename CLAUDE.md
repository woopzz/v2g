# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All development is done inside the devcontainer (VS Code: "Reopen in Container").

### Running the Application

```bash
uv sync                         # Install/update packages
python -m v2g.server            # Start FastAPI server (port 8000)
./scripts/run_workers.sh        # Start Celery workers (separate terminal)
```

### Testing

```bash
pytest ./tests/                                       # Run all tests
pytest ./tests/test_conversion.py                     # Run a single test file
pytest ./tests/test_conversion.py::test_name          # Run a single test
```

Tests use real MongoDB and LocalStack (S3/SQS) instances. The test docker-compose at `tests/docker-compose.yml` provides the required services when running outside the devcontainer.

### Linting

```bash
ruff check /app/src /app/tests    # Lint
ruff format /app/src /app/tests   # Format
```

Ruff config (`.ruff.toml`): 100 char line length, single quotes.

## Architecture

**v2g** is an async REST API that converts uploaded videos to GIFs using FFmpeg. The conversion runs as an async background task, and clients can optionally receive a webhook notification on completion.

### Request Flow

1. **Auth**: JWT (HS256) via `POST /api/v1/auth/access-token/`. Tokens last 7 days.
2. **Upload**: `POST /api/v1/conversions/` accepts multipart video + optional `webhook_url`. File stored in S3. Rate-limited per user (50/day, 10/hour) via Redis.
3. **Convert**: A Celery task (`tasks.py`) runs FFmpeg asynchronously. Status updates (`processing`/`done`/`failed`) are published to a Redis pub/sub channel. On completion, the GIF is uploaded to S3 and the conversion record updated with a presigned URL.
4. **WebSocket**: `GET /api/v1/ws/` — authenticated clients subscribe to their per-user Redis channel and receive real-time conversion status events.
5. **Webhook**: If `webhook_url` was provided, a second Celery task POSTs conversion metadata with exponential backoff (max 8 retries).
6. **Retrieve**: The conversion response includes a `gif_url` presigned S3 URL (valid 7 days) once the GIF is ready.

### Key Infrastructure

- **FastAPI** app factory in `src/v2g/app.py`; Uvicorn entry point in `server.py`
- **MongoDB** (Motor async client) for users and conversion metadata
- **AWS S3** — stores uploaded video files and output GIFs; files are accessed via presigned URLs (expiry 7 days)
- **AWS SQS** — Celery broker; **LocalStack** provides SQS and S3 locally (devcontainer env vars point to `http://localstack:4566`)
- **Redis** — DB 1 for rate limiting; async client for WebSocket pub/sub
- **Celery** workers run the FFmpeg conversion (synchronous subprocess, 180s timeout)
- **Nginx** at port 80 reverse-proxies to the app and Grafana

### Code Organization

```
src/v2g/
├── app.py, server.py          # App factory and entry point
├── tasks.py                   # Celery task definitions
├── core/                      # Shared infrastructure (config, DB, security, repository base)
└── modules/                   # Feature modules: auth/, users/, conversions/, websocket/
    └── <module>/
        ├── routes.py          # FastAPI route handlers
        ├── models.py          # Pydantic schemas
        ├── repositories.py    # Database access layer
        └── dependencies.py    # Dependency injection helpers
```

Each module follows: **routes → repositories → MongoDB**. Repositories extend `core/repository.py:BaseRepository`. The `websocket/` module is an exception — it has only `routes.py` and uses Redis pub/sub rather than MongoDB.

### Configuration

All settings use the `V2G_` prefix (defined in `core/config.py`). Key settings:

| Variable | Default | Purpose |
|---|---|---|
| `V2G_SECRET` | (required) | JWT signing secret |
| `V2G_MONGODB_HOST` | `mongo` | MongoDB host |
| `V2G_REDIS_HOST` | `redis` | Redis host |
| `V2G_SQS_REGION` | `eu-central-1` | AWS SQS region for Celery broker |
| `V2G_S3_BUCKET` | `v2g` | S3 bucket name for video/GIF storage |
| `V2G_S3_PRESIGNED_URL_EXPIRY` | `604800` (7 days) | Presigned URL validity in seconds |
| `V2G_CONVERSION_PROCESS_TIMEOUT_IN_SECONDS` | `180` | FFmpeg timeout |
| `V2G_LOG_JSON` | `false` | Enable JSON structured logs |
| `V2G_RATE_LIMIT_ENABLED` | `true` | Toggle rate limiting |

### Monitoring

Prometheus metrics are exposed at `/metrics`. Grafana (port 3000, proxied via Nginx at `/grafana/`) visualizes metrics from Prometheus and logs from Loki. Alloy collects logs from Docker containers labeled `project=v2g`.
