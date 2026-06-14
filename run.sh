#!/bin/sh
set -eu

python manage.py migrate --no-input

DJANGO_COLLECT_STATIC=1 python manage.py collectstatic --no-input

exec gunicorn \
    --worker-class gthread \
    --workers "${GUNICORN_WORKERS:-3}" \
    --threads "${GUNICORN_THREADS:-4}" \
    --timeout "${GUNICORN_TIMEOUT:-90}" \
    --graceful-timeout "${GUNICORN_GRACEFUL_TIMEOUT:-30}" \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile - \
    --no-control-socket \
    ecstasy_project.wsgi:application
