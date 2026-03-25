import requests
from celery import shared_task

from apps.notifications.models import TelegramNotification, WebhookNotification


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


@shared_task(ignore_result=True)
def send_webhook_notification(wh_notification_id: int, message_text: str):
    try:
        wh_notification = WebhookNotification.objects.get(id=wh_notification_id)
    except WebhookNotification.DoesNotExist:
        print(f"❌ Webhook notification with id {wh_notification_id} does not exist.")
        return

    headers: dict[str, str] = {}
    for header_row in (wh_notification.headers or "").split("\n"):
        key, value = header_row.split(":")
        headers[key.strip()] = value.strip()

    if wh_notification.proxy_url:
        proxies = {"http": wh_notification.proxy_url, "https": wh_notification.proxy_url}
    else:
        proxies = None

    resp = requests.request(
        url=wh_notification.url,
        method=wh_notification.method,
        proxies=proxies,
        data=message_text,
        headers=headers,
        timeout=wh_notification.timeout,
    )

    if resp.status_code != 200:
        print(
            f"❌ Error sending webhook notification. "
            f"Status code: {resp.status_code}. Reason: {resp.text!r}. Headers: {headers!r}. "
            f"URL: {wh_notification.url!r}. Data: {message_text!r}. Timeout: {wh_notification.timeout}"
        )
    else:
        print("✅ Webhook notification sent successfully.")
