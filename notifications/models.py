from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group as UserGroup
from django.db import models
from django.utils.safestring import mark_safe

from check.models import DeviceGroup, Devices
from ecstasy_project.types.models import DateTimeModel


class TelegramNotification(DateTimeModel):
    name = models.CharField(max_length=512, verbose_name="Название оповещения")

    telegram_api_url = models.CharField(
        max_length=2048, default="https://api.telegram.org/", verbose_name="Telegram API URL"
    )
    bot_token = models.CharField(max_length=256)
    chat_id = models.CharField(
        max_length=256,
        help_text="Уникальный идентификатор целевого чата или имя пользователя целевого канала.",
    )
    message_thread_id = models.BigIntegerField(
        help_text="Уникальный идентификатор целевой ветки сообщений (темы) форума; только для супергрупп-форумов.",
        null=True,
        blank=True,
    )
    business_connection_id = models.CharField(
        max_length=256,
        help_text="Уникальный идентификатор бизнес-аккаунта, от которого было получено сообщение. "
        "Если значение не пустое, сообщение относится к чату соответствующего бизнес-аккаунта, "
        "который не связан с потенциальным ботом, который может иметь тот же идентификатор.",
        null=True,
        blank=True,
    )

    class ParseModeChoices(models.TextChoices):
        HTML = "HTML"
        Markdown = "Markdown"
        MarkdownV2 = "MarkdownV2"

    parse_mode = models.CharField(
        max_length=16, default=ParseModeChoices.HTML, choices=ParseModeChoices.choices  # noqa
    )

    active = models.BooleanField(default=True, help_text="Активно ли оповещение.")
    disable_notification = models.BooleanField(
        default=False, help_text="Отправляет сообщение беззвучно. Пользователи получат уведомление без звука."
    )
    protect_content = models.BooleanField(
        default=False, help_text="Защищает содержимое отправленного сообщения от пересылки и сохранения."
    )

    message_effect_id = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        help_text="Уникальный идентификатор эффекта сообщения, который будет добавлен к сообщению;"
        " только для личных чатов",
    )

    text = models.TextField(
        max_length=4096,
        help_text="Текст отправляемого сообщения. 1-4096 символов после обработки сущностей!\n"
        "Поддерживается шаблонизатор Django, передаваемые объекты: device, result, request, user",
    )

    reply_markup = models.JSONField(
        null=True,
        blank=True,
        help_text="Дополнительные параметры интерфейса. Объект в формате JSON для встроенной клавиатуры,"
        " пользовательской клавиатуры ответа, инструкций по удалению клавиатуры ответа"
        " или принудительному ответу от пользователя",
    )

    notification_conditions = models.ManyToManyField(
        "NotificationCondition",
        related_name="telegram_notifications",
        help_text="Если условий несколько, то будет выбрано хотя бы одно сработанное.\nРеализуется логическое ИЛИ.",
    )  # type: ignore

    def __str__(self):
        return f"Telegram Notification: {self.name}"

    def __repr__(self):
        return self.__str__()

    class Meta:
        db_table = "notifications_by_telegram"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["active"], name="notif_telegram_active_index"),
        ]


class NotificationTrigger(models.Model):
    """Класс для хранения названия действия, которое триггерит оповещения."""

    name = models.CharField(max_length=64, primary_key=True)
    description = models.CharField(max_length=256)

    def __str__(self):
        return f"{self.name} | {self.description}"

    def __repr__(self):
        return self.__str__()

    class Meta:
        db_table = "notification_triggers"


class NotificationCondition(DateTimeModel):
    name = models.CharField(
        max_length=512,
        verbose_name="Название условия",
        help_text=mark_safe(
            'Смотрите <a href="https://github.com/ig-rudenko/ecstasy/wiki" target="_blank">wiki</a>'
        ),
    )
    active = models.BooleanField(default=True, help_text="Включает проверку данного условия.")

    devices = models.ManyToManyField(
        Devices,
        verbose_name="Перечень оборудования",
        blank=True,
        related_name="notification_conditions",
        help_text="Перечень конкретного оборудования, если не указано, то все.",
    )
    devices_groups = models.ManyToManyField(
        DeviceGroup,
        verbose_name="Группы оборудования",
        blank=True,
        related_name="notification_conditions",
        help_text="Перечень групп оборудования, если не указано, то все.",
    )
    users = models.ManyToManyField(
        get_user_model(),
        verbose_name="Пользователи",
        blank=True,
        related_name="notification_conditions",
    )  # type: ignore
    users_groups = models.ManyToManyField(
        UserGroup,
        verbose_name="Группы пользователей",
        blank=True,
        related_name="notification_conditions",
        help_text="Перечень групп пользователей, если не указано, то все.",
    )

    triggers = models.ManyToManyField(
        NotificationTrigger,
        verbose_name="Триггеры",
        blank=False,
        related_name="notification_conditions",
        help_text="Какие действия будут провоцировать оповещение.",
    )

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return self.__str__()

    class Meta:
        db_table = "notification_conditions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["active"], name="notif_cond_active_index"),
        ]
