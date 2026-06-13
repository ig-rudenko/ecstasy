from celery import shared_task
from django.contrib.sessions.models import Session
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.utils import aware_utcnow


@shared_task
def flush_expired_tokens():
    """Flushes any expired tokens in the outstanding token list"""
    return OutstandingToken.objects.filter(expires_at__lte=aware_utcnow()).delete()


@shared_task
def flush_expired_cookie_sessions():
    """Flushes any expired cookies"""
    return Session.objects.filter(expire_date__lte=aware_utcnow()).delete()
