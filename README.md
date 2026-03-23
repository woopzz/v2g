# Video to GIF API (`v2g`)

> A simple and scalable web API to convert video files into animated GIF images.

This project provides a backend service that takes video files (e.g., MP4, MOV) and converts them into GIFs. It’s built with modern tooling and deployment infrastructure so you can run it locally or in a production environment.

## 🚀 Features

- 🎥 Accepts common video formats and produces GIF output.
- 🐳 Docker-ready and easy to deploy.
- 📦 Includes infrastructure support (Terraform, Docker Compose).
- 🔁 Background task processing with Celery and SQS.
- 🔔 Real-time WebSocket notifications for conversion status updates.
- 📊 Monitoring with Grafana, Alloy and Prometheus.
- 📁 Integrated tests.

## 🧱 Architecture

This project combines:

- **FastAPI** – for the HTTP API server
- **Celery** – for asynchronous video conversion tasks
- **AWS SQS** – as the Celery broker (LocalStack used locally)
- **AWS S3** – for storing video and GIF files (LocalStack used locally)
- **Redis** – for rate limiting and WebSocket pub/sub
- **MongoDB** – for storing conversion metadata and job status
- **Docker and Docker Compose** – for local development and deployment
- **Terraform** – for infrastructure provisioning
- **Grafana, Alloy and Prometheus** – for observability

## 📦 Getting Started

### 🛠 Prerequisites

Make sure you have installed:

- Docker
- Docker Compose

### 🏡 Local Development

1. Use devcontainer.
2. Run `uv sync` to install / update packages.
3. Run [./scripts/run_workers.sh](./scripts/run_workers.sh) to spawn Celery workers.

## 🧪 Running Tests

```bash
# Inside of devcontainer.
uv sync  # If you didn't do it before.
pytest ./tests/
```

## 🐳 Deployment

1. Use Terraform files from the [./terraform](./terraform/) directory to spawn an EC2 instance.
2. Clone the repo.
    ```bash
    git clone https://github.com/woopzz/v2g.git
    cd v2g
    ```
3. Start services.
    ```bash
    docker compose up --build
    ```
4. Visit the API.
    ```bash
    http://localhost/docs
    ```

> Go through the docker compose file [./docker-compose.yaml](./docker-compose.yaml) and the config file [./src/v2g/core/config.py](./src/v2g/core/config.py) to be aware of settings you can change with environment variables.
