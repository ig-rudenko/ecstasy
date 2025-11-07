python manage.py migrate --no-input;

export DJANGO_COLLECT_STATIC=1;
python manage.py collectstatic --no-input;
export DJANGO_COLLECT_STATIC=0;

python manage.py createsuperuser --noinput;
gunicorn --workers "$GUNICORN_WORKERS" --bind 0.0.0.0:8000 ecstasy_project.wsgi:application;
