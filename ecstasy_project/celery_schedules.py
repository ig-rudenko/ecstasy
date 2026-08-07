from django.conf import settings
from django_celery_beat.models import CrontabSchedule


def get_crontab_schedule(
    *,
    minute: str,
    hour: str,
    day_of_week: str = "*",
    day_of_month: str = "*",
    month_of_year: str = "*",
    timezone: str | None = None,
) -> CrontabSchedule:
    """Вернуть cron-расписание или создать его без ошибки при исторических дубликатах."""

    schedule_fields = {
        "minute": minute,
        "hour": hour,
        "day_of_week": day_of_week,
        "day_of_month": day_of_month,
        "month_of_year": month_of_year,
        "timezone": timezone or settings.CELERY_TIMEZONE,
    }
    crontab = CrontabSchedule.objects.filter(**schedule_fields).order_by("id").first()

    return crontab or CrontabSchedule.objects.create(**schedule_fields)
