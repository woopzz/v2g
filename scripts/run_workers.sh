#!/bin/bash
/app/.venv/bin/celery -A v2g.tasks worker --loglevel=info --concurrency=1 -Q conversion
