from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecstasy_project.settings')
app = Celery('ecstasy_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
