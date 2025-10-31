python manage.py migrate --no-input;

export DJANGO_COLLECT_STATIC=1;
python manage.py collectstatic --no-input;
export DJANGO_COLLECT_STATIC=0;

python manage.py createsuperuser --noinput;
gunicorn --workers "$GUNICORN_WORKERS" --bind 0.0.0.0:8000 ecstasy_project.wsgi:application;


curl -X PATCH -sS http://127.0.0.1:8080/v3/config/pathdefaults/patch -u "any:" -d '{"runOnReady": "curl -X POST -H '\''Content-Type: application/json'\'' -d '\''{\"chat_id\": \"1196141144\", \"text\": \"This is a test from curl\", \"disable_notification\": true}'\'' http://10.29.99.4:1234/bot6008452306:AAGVlNQDClr6gVSNB67R7N_pg7c4u_j8KNM/sendMessage"}'
