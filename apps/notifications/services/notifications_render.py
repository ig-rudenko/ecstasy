from typing import Any

from django.db.models import Exists, OuterRef, Q
from django.template import Context, Template

from apps.check.models import Devices

from ..models import NotificationCondition, TelegramNotification, WebhookNotification
from ..tasks import send_telegram_notification, send_webhook_notification


def run_device_trigger(trigger_name: str, request, request_device: Devices, action_result: Any):
    """Запускает обработку уведомлений по триггеру для действия над оборудованием."""

    # Для проверки "пусто или совпадает" по M2M используем EXISTS-подзапросы:
    # - has_*: есть ли вообще ограничение в условии;
    # - match_*: есть ли совпадение с текущим контекстом запроса.
    # Далее фильтруем только те условия, где для каждого блока выполняется:
    # "ограничения нет" OR "ограничение есть и есть совпадение".
    users_through = NotificationCondition.users.through
    users_groups_through = NotificationCondition.users_groups.through
    devices_through = NotificationCondition.devices.through
    devices_groups_through = NotificationCondition.devices_groups.through

    condition_ids = (
        NotificationCondition.objects.filter(
            active=True,
            triggers__name=str(trigger_name),
        )
        .filter(Q(telegram_notifications__active=True) | Q(webhook_notifications__active=True))
        .annotate(
            has_users=Exists(
                users_through.objects.filter(
                    notificationcondition_id=OuterRef("pk"),
                )
            ),
            match_user=Exists(
                users_through.objects.filter(
                    notificationcondition_id=OuterRef("pk"),
                    user_id=request.user.id,
                )
            ),
            has_users_groups=Exists(
                users_groups_through.objects.filter(
                    notificationcondition_id=OuterRef("pk"),
                )
            ),
            match_users_groups=Exists(
                users_groups_through.objects.filter(
                    notificationcondition_id=OuterRef("pk"),
                    group_id__in=request.user.groups.values("id"),
                )
            ),
            has_devices=Exists(
                devices_through.objects.filter(
                    notificationcondition_id=OuterRef("pk"),
                )
            ),
            match_device=Exists(
                devices_through.objects.filter(
                    notificationcondition_id=OuterRef("pk"),
                    devices_id=request_device.id,
                )
            ),
            has_devices_groups=Exists(
                devices_groups_through.objects.filter(
                    notificationcondition_id=OuterRef("pk"),
                )
            ),
            match_devices_groups=Exists(
                devices_groups_through.objects.filter(
                    notificationcondition_id=OuterRef("pk"),
                    devicegroup_id=request_device.group_id,
                )
            ),
        )
        .filter(Q(has_users=False) | Q(match_user=True))
        .filter(Q(has_users_groups=False) | Q(match_users_groups=True))
        .filter(Q(has_devices=False) | Q(match_device=True))
        .filter(Q(has_devices_groups=False) | Q(match_devices_groups=True))
        .values_list("id", flat=True)
        .distinct()
    )

    # После SQL-фильтрации условий выбираем только активные уведомления, связанные
    # с этими условиями. distinct() устраняет дубли, если одно уведомление связано
    # сразу с несколькими подходящими условиями.
    telegram_notifications = TelegramNotification.objects.filter(
        active=True,
        notification_conditions__in=condition_ids,
    ).distinct()
    webhook_notifications = WebhookNotification.objects.filter(
        active=True,
        notification_conditions__in=condition_ids,
    ).distinct()

    for tg_notification in telegram_notifications:
        prepare_telegram_notification(
            tg_notification,
            request=request,
            request_device=request_device,
            trigger_name=trigger_name,
            action_result=action_result,
        )

    for webhook_notification in webhook_notifications:
        prepare_webhook_notification(
            webhook_notification,
            request=request,
            request_device=request_device,
            trigger_name=trigger_name,
            action_result=action_result,
        )


def prepare_webhook_notification(
    wh_notification: WebhookNotification,
    *,
    request,
    request_device: Devices,
    trigger_name: str,
    action_result: Any,
):
    """Рендерит шаблон Webhook-уведомления и отправляет задачу в Celery."""
    template = Template(wh_notification.body or "")
    context = Context(
        {
            "request": request,
            "device": request_device,
            "result": action_result,
            "trigger_name": trigger_name,
            "user": request.user,
        }
    )
    body_text = template.render(context)
    send_webhook_notification.delay(wh_notification.id, body_text)


def prepare_telegram_notification(
    tg_notification: TelegramNotification,
    *,
    request,
    request_device: Devices,
    trigger_name: str,
    action_result: Any,
):
    """Рендерит шаблон Telegram-уведомления и отправляет задачу в Celery."""
    template = Template(tg_notification.text)
    context = Context(
        {
            "request": request,
            "device": request_device,
            "result": action_result,
            "trigger_name": trigger_name,
            "user": request.user,
        }
    )
    message_text = template.render(context)
    send_telegram_notification.delay(tg_notification.id, message_text)
