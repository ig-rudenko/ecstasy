from django.contrib import admin
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.utils.safestring import mark_safe

from .models import UserAPIToken


@admin.register(UserAPIToken)
class CustomTokenAdmin(admin.ModelAdmin):
    list_display = ("verbose_info", "description", "created", "last_used", "expired", "verbose_allowed_ips")
    search_fields = ("user__username", "description")
    readonly_fields = ("key", "last_used")
    ordering = ("-created",)

    fieldsets = (
        (
            "Настройки",
            {"fields": ("user", "description", "expired", "last_used", "allowed_ips")},
        ),
        (
            "Ключ",
            {"fields": ("key",)},
        ),
    )

    @admin.display()
    def verbose_info(self, obj: UserAPIToken):
        status = "❌" if obj.expired and obj.expired < timezone.now() else "✅"
        return f"{status} {obj.user}"

    @admin.display()
    def verbose_allowed_ips(self, obj: UserAPIToken):
        return mark_safe("<br>".join(obj.allowed_ips.split(",")))


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    def _session_data(self, obj):
        return obj.get_decoded()

    list_display = ["session_key", "_session_data", "expire_date"]
