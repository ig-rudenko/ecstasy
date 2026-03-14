import requests
from celery import shared_task

from notifications.models import TelegramNotification


@shared_task(ignore_result=True)
def send_telegram_notification(tg_notification_id: int, message_text: str):
    try:
        tg_notification = TelegramNotification.objects.get(id=tg_notification_id)
    except TelegramNotification.DoesNotExist:
        print(f"❌ Telegram notification with id {tg_notification_id} does not exist.")
        return

    api_url = tg_notification.telegram_api_url
    if not api_url.endswith("/"):
        api_url += "/"

    data = {
        "business_connection_id": tg_notification.business_connection_id,
        "chat_id": tg_notification.chat_id,
        "message_thread_id": tg_notification.message_thread_id,
        "text": message_text,
        "parse_mode": tg_notification.parse_mode,
        "disable_notification": tg_notification.disable_notification,
        "protect_content": tg_notification.protect_content,
        "message_effect_id": tg_notification.message_effect_id,
        "reply_markup": tg_notification.reply_markup,
    }

    # Удаляем все пустые ключи
    for key, value in list(data.items()):
        if value is None:
            del data[key]

    resp = requests.post(
        f"{tg_notification.telegram_api_url}bot{tg_notification.bot_token}/sendMessage",
        json=data,
        headers={"Content-Type": "application/json"},
        timeout=5,
    )

    if resp.status_code != 200:
        print(
            f"❌ Error sending telegram notification. "
            f"Status code: {resp.status_code}. Reason: {resp.text!r}. Data: {data!r}"
        )
    else:
        print("✅ Telegram notification sent successfully.")
