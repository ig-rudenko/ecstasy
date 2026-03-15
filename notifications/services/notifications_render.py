from typing import Any

from django.template import Context, Template

from check.models import Devices

from ..models import NotificationCondition, TelegramNotification
from ..tasks import send_telegram_notification


def run_device_trigger(trigger_name: str, request, request_device: Devices, action_result: Any):
    """Запускает обработку событий триггера, связанного с действиями над оборудованием."""

    conditions = (
        NotificationCondition.objects.filter(
            active=True,
            triggers__name=trigger_name,
            telegram_notifications__active=True,
        )
        .prefetch_related("users", "users_groups", "devices", "devices_groups")
        .distinct()
    )

    telegram_notifications = set()

    for condition in conditions:

        # -------------- USERS --------------
        condition_users_ids = set(condition.users.all().values_list("id", flat=True))
        if condition_users_ids and request.user.id not in condition_users_ids:
            # Если в условии имеется перечень пользователей,
            # но не нашли пользователя, который сделал запрос среди перечня пользователей с условием,
            # тогда данное условие не подходит.
            break

        # -------------- USERS GROUPS --------------
        request.user_groups_ids = set(request.user.groups.all().values_list("id", flat=True))
        condition_user_groups_ids = set(condition.users_groups.all().values_list("id", flat=True))
        if condition_user_groups_ids and not request.user_groups_ids & condition_user_groups_ids:
            # Если в условии имеется перечень групп пользователей,
            # но у входного пользователя не нашли хотя бы одну группу, которая пересекается с необходимыми,
            # тогда данное условие не подходит.
            break

        # -------------- DEVICES --------------
        condition_devices_ids = set(condition.devices.all().values_list("id", flat=True))
        if condition_devices_ids and request_device.id not in condition_devices_ids:
            # Если в условии имеется перечень оборудования,
            # но не нашли оборудование, которое выполнило действие среди этого перечня,
            # тогда данное условие не подходит.
            break

        # -------------- DEVICES GROUPS --------------
        condition_devices_groups_ids = set(condition.devices_groups.all().values_list("id", flat=True))
        if condition_devices_groups_ids and request_device.group_id not in condition_devices_groups_ids:
            # Если в условии имеется перечень групп оборудования,
            # но у входного оборудования группа не находится в списке,
            # тогда данное условие не подходит.
            break

        # Добавляем оповещения телеграмм, которые прошли проверку условий.
        telegram_notifications.update(condition.telegram_notifications.filter(active=True))  # type: ignore

    for tg_notification in telegram_notifications:
        prepare_telegram_notification(tg_notification, request, request_device, action_result)


def prepare_telegram_notification(
    tg_notification: TelegramNotification, request, request_device: Devices, action_result: Any
):
    template = Template(tg_notification.text)
    context = Context(
        {
            "request": request,
            "device": request_device,
            "result": action_result,
            "user": request.user,
        }
    )
    message_text = template.render(context)
    send_telegram_notification.delay(tg_notification.id, message_text)
