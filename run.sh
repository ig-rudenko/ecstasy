#!/bin/sh
python manage.py migrate --no-input

export DJANGO_COLLECT_STATIC=1
python manage.py collectstatic --no-input
export DJANGO_COLLECT_STATIC=0

exec gunicorn --workers "${GUNICORN_WORKERS:-5}" --bind 0.0.0.0:8000 ecstasy_project.wsgi:application --no-control-socket
