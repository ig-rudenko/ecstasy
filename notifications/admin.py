from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import NotificationCondition, TelegramNotification


@admin.register(TelegramNotification)
class TelegramNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "active",
        "bot_token_preview",
        "chat_id",
        "conditions_count",
        "created_at",
    )
    list_filter = ("active", "parse_mode", "disable_notification", "protect_content", "created_at")
    search_fields = ("name", "bot_token", "chat_id", "text")
    readonly_fields = ("created_at", "updated_at")
    filter_horizontal = ("notification_conditions",)

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": ("name", "active"),
            },
        ),
        (
            "Настройки Telegram",
            {
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
                "fields": ("notification_conditions",),
            },
        ),
        (
            "Мета-информация",
            {
                "classes": ("collapse",),
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    @admin.display(description="Превью токена бота")
    def bot_token_preview(self, obj: TelegramNotification):
        if obj.bot_token:
            return f"{obj.bot_token[:10]}..."
        return "-"

    @admin.display(description="Кол-во условий")
    def conditions_count(self, obj: TelegramNotification):
        return obj.notification_conditions.count()


@admin.register(NotificationCondition)
class NotificationConditionAdmin(admin.ModelAdmin):
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
    list_filter = ("active", "created_at", "devices", "devices_groups", "users", "users_groups")
    search_fields = ("name", "devices__name", "devices_groups__name", "users__username", "triggers__name")
    filter_horizontal = ("devices", "devices_groups", "users", "users_groups", "triggers")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Общая информация",
            {
                "fields": ("name", "active"),
            },
        ),
        (
            "Фильтрация по оборудованию",
            {
                "fields": ("devices", "devices_groups"),
            },
        ),
        (
            "Фильтрация по пользователям",
            {
                "fields": ("users", "users_groups"),
            },
        ),
        (
            "Триггеры",
            {
                "fields": ("triggers",),
            },
        ),
        (
            "Мета-информация",
            {
                "classes": ("collapse",),
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    @admin.display(description="Устройства")
    def devices_count(self, obj: NotificationCondition):
        return self._get_html_list_values(obj, "devices", "name")

    @admin.display(description="Группы устройств")
    def devices_groups_count(self, obj):
        return self._get_html_list_values(obj, "devices_groups", "name")

    @admin.display(description="Пользователи")
    def users_count(self, obj):
        return self._get_html_list_values(obj, "users", "username")

    @admin.display(description="Группы пользователей")
    def users_groups_count(self, obj):
        return self._get_html_list_values(obj, "users_groups", "name")

    @admin.display(description="Триггеры")
    def triggers_list(self, obj):
        return self._get_html_list_values(obj, "triggers", "name")

    @staticmethod
    def _get_html_list_values(obj, value_name: str, field_name: str) -> str:
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
