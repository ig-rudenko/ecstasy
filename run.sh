python manage.py migrate --no-input;
python manage.py collectstatic --settings ecstasy_project.init_settings --no-input;
gunicorn --workers 5 --bind 0.0.0.0:8000 ecstasy_project.wsgi:application