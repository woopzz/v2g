# Video to GIF

A web API that converts video files into GIF images.

### An example configuration

```yaml
services:

  mongo:
    image: mongo:8.2
    volumes:
      - mongo-data:/data/db

  redis:
    image: redis:8.4

  app:
    image: ghcr.io/woopzz/v2g:latest
    ports:
      - "8000:8000"
    depends_on:
      - mongo
      - redis

  workers:
    image: ghcr.io/woopzz/v2g:latest
    depends_on:
      - mongo
      - redis
    command: /app/run_workers.sh

volumes:
  mongo-data:
```

### Development

Use devcontainer.

Spawn Celery workers manually by running [./scripts/run_workers.sh](./scripts/run_workers.sh).
