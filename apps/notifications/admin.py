from django.contrib import admin
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import ChoicesDropdownFilter, MultipleRelatedDropdownFilter, RangeDateTimeFilter

from ecstasy_project.admin_filters import distinct_dropdown_filter

from .models import (
    NotificationCondition,
    NotificationTrigger,
    TelegramNotification,
    WebhookNotification,
)

MethodDropdownFilter = distinct_dropdown_filter("method", "method")


@admin.register(WebhookNotification)
class WebhookNotificationAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = True
    list_display = (
        "name",
        "active",
        "url_preview",
        "method",
        "proxy_url",
        "timeout",
        "conditions_count",
        "created_at",
    )
    list_filter = ("active", MethodDropdownFilter, ("created_at", RangeDateTimeFilter))
    search_fields = ("name", "url", "body", "headers")
    readonly_fields = ("created_at", "updated_at")
    filter_horizontal = ("notification_conditions",)

    fieldsets = (
        (
            "Основная информация",
            {
                "classes": ("tab",),
                "fields": ("name", "active"),
            },
        ),
        (
            "Настройки вебхука",
            {
                "classes": ("tab",),
                "fields": ("url", "proxy_url", "method", "timeout"),
            },
        ),
        (
            "Данные запроса",
            {
                "classes": ("tab",),
                "fields": ("headers", "body"),
            },
        ),
        (
            "Условия отправки",
            {
                "classes": ("tab",),
                "fields": ("notification_conditions",),
            },
        ),
        (
            "Мета-информация",
            {
                "classes": ("tab", "collapse"),
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    @admin.display(description="URL (превью)")
    def url_preview(self, obj: WebhookNotification) -> str:
        """Return a shortened URL for changelist display."""
        return obj.url if len(obj.url) < 50 else obj.url[:47] + "..."

    @admin.display(description="Кол-во условий")
    def conditions_count(self, obj: WebhookNotification) -> int:
        """Return the number of linked conditions."""
        return obj.notification_conditions.count()


@admin.register(TelegramNotification)
class TelegramNotificationAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = True
    list_display = (
        "name",
        "active",
        "bot_token_preview",
        "chat_id",
        "conditions_count",
        "created_at",
    )
    list_filter = (
        "active",
        ("parse_mode", ChoicesDropdownFilter),
        "disable_notification",
        "protect_content",
        ("created_at", RangeDateTimeFilter),
    )
    search_fields = ("name", "bot_token", "chat_id", "text")
    readonly_fields = ("created_at", "updated_at")
    filter_horizontal = ("notification_conditions",)

    fieldsets = (
        (
            "Основная информация",
            {
                "classes": ("tab",),
                "fields": ("name", "active"),
            },
        ),
        (
            "Настройки Telegram",
            {
                "classes": ("tab",),
                "fields": (
                    "telegram_api_url",
                    "bot_token",
                    "chat_id",
                    "message_thread_id",
                    "business_connection_id",
                ),
            },
        ),
        (
            "Сообщение",
            {
                "classes": ("tab",),
                "fields": (
                    "text",
                    "parse_mode",
                    "disable_notification",
                    "protect_content",
                    "message_effect_id",
                    "reply_markup",
                ),
            },
        ),
        (
            "Условия отправки",
            {
                "classes": ("tab",),
                "fields": ("notification_conditions",),
            },
        ),
        (
            "Мета-информация",
            {
                "classes": ("tab", "collapse"),
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    @admin.display(description="Превью токена бота")
    def bot_token_preview(self, obj: TelegramNotification) -> str:
        """Return a masked bot token for changelist display."""
        if obj.bot_token:
            return f"{obj.bot_token[:10]}..."
        return "-"

    @admin.display(description="Кол-во условий")
    def conditions_count(self, obj: TelegramNotification) -> int:
        """Return the number of linked conditions."""
        return obj.notification_conditions.count()


@admin.register(NotificationCondition)
class NotificationConditionAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = True
    list_display = (
        "name",
        "active",
        "devices_count",
        "devices_groups_count",
        "users_count",
        "users_groups_count",
        "triggers_list",
        "created_at",
    )
    list_filter = (
        "active",
        ("created_at", RangeDateTimeFilter),
        ("devices", MultipleRelatedDropdownFilter),
        ("devices_groups", MultipleRelatedDropdownFilter),
        ("users", MultipleRelatedDropdownFilter),
        ("users_groups", MultipleRelatedDropdownFilter),
    )
    search_fields = ("name", "devices__name", "devices_groups__name", "users__username", "triggers__name")
    filter_horizontal = ("devices", "devices_groups", "users", "users_groups", "triggers")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Общая информация",
            {
                "classes": ("tab",),
                "fields": ("name", "active"),
            },
        ),
        (
            "Фильтрация по оборудованию",
            {
                "classes": ("tab",),
                "fields": ("devices", "devices_groups"),
            },
        ),
        (
            "Фильтрация по пользователям",
            {
                "classes": ("tab",),
                "fields": ("users", "users_groups"),
            },
        ),
        (
            "Триггеры",
            {
                "classes": ("tab",),
                "fields": ("triggers",),
            },
        ),
        (
            "Мета-информация",
            {
                "classes": ("tab", "collapse"),
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    @admin.display(description="Устройства")
    def devices_count(self, obj: NotificationCondition) -> str:
        """Return selected devices as a compact HTML list."""
        return self._get_html_list_values(obj, "devices", "name")

    @admin.display(description="Группы устройств")
    def devices_groups_count(self, obj: NotificationCondition) -> str:
        """Return selected device groups as a compact HTML list."""
        return self._get_html_list_values(obj, "devices_groups", "name")

    @admin.display(description="Пользователи")
    def users_count(self, obj: NotificationCondition) -> str:
        """Return selected users as a compact HTML list."""
        return self._get_html_list_values(obj, "users", "username")

    @admin.display(description="Группы пользователей")
    def users_groups_count(self, obj: NotificationCondition) -> str:
        """Return selected user groups as a compact HTML list."""
        return self._get_html_list_values(obj, "users_groups", "name")

    @admin.display(description="Триггеры")
    def triggers_list(self, obj: NotificationCondition) -> str:
        """Return selected triggers as a compact HTML list."""
        return self._get_html_list_values(obj, "triggers", "name")

    @staticmethod
    def _get_html_list_values(obj, value_name: str, field_name: str) -> str:
        """Render selected related objects as a short HTML list."""
        max_rows = 10
        text = '<ul style="font-family: monospace;">'
        total_count = getattr(obj, value_name).count()
        if not total_count:
            return "Все"

        for value in getattr(obj, value_name).all()[:10].values_list(field_name, flat=True):
            text += f"<li>{value}</li>"
        if total_count > max_rows:
            text += f"<span>и ещё {total_count - max_rows}</span>"
        text += "</ul>"
        return mark_safe(text)


@admin.register(NotificationTrigger)
class NotificationTriggerAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_display = ("name", "description", "conditions_count")
    search_fields = ("name", "description")

    @admin.display(description="Кол-во условий")
    def conditions_count(self, obj: NotificationTrigger) -> int:
        """Return the number of conditions linked to the trigger."""
        return obj.notification_conditions.count()
