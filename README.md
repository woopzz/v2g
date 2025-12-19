# Video to GIF

A web API that converts video files into GIF images.

### An example configuration

```yaml
services:

  mongo:
    image: mongo:8.2
    volumes:
      - mongo-data:/data/db
    labels:
      project: "${PROJECT:-v2g}"

  redis:
    image: redis:8.4
    labels:
      project: "${PROJECT:-v2g}"

  app:
    image: ghcr.io/woopzz/v2g:latest
    depends_on:
      - mongo
      - redis
    environment:
      V2G_LOG_JSON: 1
    labels:
      project: "${PROJECT:-v2g}"

  workers:
    image: ghcr.io/woopzz/v2g:latest
    depends_on:
      - mongo
      - redis
    environment:
      V2G_LOG_JSON: 1
    labels:
      project: "${PROJECT:-v2g}"
    command: /app/run_workers.sh

  prometheus:
    image: prom/prometheus:v3.8.0
    volumes:
      - ./prometheus:/etc/prometheus
      - prometheus-data:/prometheus
    labels:
      project: "${PROJECT:-v2g}"
    command:
      - '--config.file=/etc/prometheus/prometheus.yaml'

  node_exporter:
    image: prom/node-exporter:v1.10.2
    pid: host
    volumes:
      - '/:/host:ro,rslave'
    labels:
      project: "${PROJECT:-v2g}"
    command:
      - '--path.rootfs=/host'

  loki:
    image: grafana/loki:3.5.9
    volumes:
      - loki-data:/loki
    labels:
      project: "${PROJECT:-v2g}"

  alloy:
    image: grafana/alloy:v1.12.0
    volumes:
      - ./alloy/config.alloy:/etc/alloy/config.alloy
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    labels:
      project: "${PROJECT:-v2g}"
    command: run /etc/alloy/config.alloy

  grafana:
    image: grafana/grafana:12.3.0
    depends_on:
      - alloy
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning
      - grafana-data:/var/lib/grafana
    environment:
      GF_SECURITY_ADMIN_USER: "${GF_SECURITY_ADMIN_USER:-admin}"
      GF_SECURITY_ADMIN_PASSWORD: "${GF_SECURITY_ADMIN_PASSWORD:-admin}"
      GF_SERVER_ROOT_URL: http://grafana:3000/grafana/
      GF_SERVER_SERVE_FROM_SUB_PATH: true
    labels:
      project: "${PROJECT:-v2g}"

  nginx:
    image: nginx:1.29.4
    ports:
      - "80:80"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
    depends_on:
      - app

volumes:
  mongo-data:
  prometheus-data:
  loki-data:
  grafana-data:
```

### Development

Use devcontainer.

Spawn Celery workers manually by running [./scripts/run_workers.sh](./scripts/run_workers.sh).
