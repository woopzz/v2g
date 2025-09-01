# Video to GIF

A web API that converts video files into GIF images.

### How to use

You will need Docker (and Docker Compose) to run the app.

1. Create a .env file in the project root with at least the SECRET key. Check `./v2g/config.py` for other configurable options.
```
SECRET=YOUR_SECRET
```
2. Start the app:
```bash
docker compose up
```
3. Open `http://0.0.0.0:8000/docs` to view the Swagger documentation.

### Development

Use the devcontainer.

There is no separate instance for Celery workers - you need to manage them manually inside the app instance. Run the script `./scripts/run_workers.sh` to spawn the workers.
