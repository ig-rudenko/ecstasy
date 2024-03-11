from celery import shared_task
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.utils import aware_utcnow


@shared_task
def flush_expired_tokens():
    """Flushes any expired tokens in the outstanding token list"""
    OutstandingToken.objects.filter(expires_at__lte=aware_utcnow()).delete()
