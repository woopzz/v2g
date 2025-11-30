#!/bin/bash
/app/.venv/bin/celery -A v2g.tasks worker --loglevel=info --concurrency=${V2G_CELERY_CONCURRENCY:-1} -P prefork
