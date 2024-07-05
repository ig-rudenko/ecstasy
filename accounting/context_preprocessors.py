from django.conf import settings


def ecstasy_loop_url(request):
    return {"ecstasy_loop_url": settings.ECSTASY_LOOP_URL}
