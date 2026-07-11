#!/bin/sh
set -e

python manage.py migrate --noinput

exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-4}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile - \
    --log-level "${GUNICORN_LOG_LEVEL:-info}"
