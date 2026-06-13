#!/bin/sh
set -eu

python manage.py migrate --no-input

DJANGO_COLLECT_STATIC=1 python manage.py collectstatic --no-input

exec gunicorn \
    --workers "${GUNICORN_WORKERS:-5}" \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile - \
    --no-control-socket \
    ecstasy_project.wsgi:application
