#!/bin/bash
celery -A v2g.tasks worker --loglevel=info --concurrency=5 -Q conversion
