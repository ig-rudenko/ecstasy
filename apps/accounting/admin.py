from django.contrib import admin
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import RangeDateTimeFilter

from .models import UserAPIToken


@admin.register(UserAPIToken)
class CustomTokenAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_display = ("verbose_info", "description", "created", "last_used", "expired", "verbose_allowed_ips")
    search_fields = ("user__username", "description")
    readonly_fields = ("key", "last_used")
    ordering = ("-created",)
    autocomplete_fields = ("user",)
    list_filter_submit = True
    list_filter = (
        ("created", RangeDateTimeFilter),
        ("last_used", RangeDateTimeFilter),
        ("expired", RangeDateTimeFilter),
    )
    fieldsets = (
        (
            "Настройки",
            {
                "classes": ("tab",),
                "fields": ("user", "description", "expired", "last_used", "allowed_ips"),
            },
        ),
        (
            "Ключ",
            {
                "classes": ("tab",),
                "fields": ("key",),
            },
        ),
    )

    @admin.display()
    def verbose_info(self, obj: UserAPIToken) -> str:
        """Return token owner with a simple status marker."""
        status = "❌" if obj.expired and obj.expired < timezone.now() else "✅"
        return f"{status} {obj.user}"

    @admin.display()
    def verbose_allowed_ips(self, obj: UserAPIToken) -> str:
        """Render allowed IPs in multiple lines."""
        return mark_safe("<br>".join(obj.allowed_ips.split(",")))


@admin.register(Session)
class SessionAdmin(ModelAdmin):
    compressed_fields = True
    list_display = ["session_key", "_session_data", "expire_date"]
    search_fields = ["session_key"]
    readonly_fields = ["session_key", "_session_data", "expire_date"]
    list_filter_submit = True
    list_filter = (("expire_date", RangeDateTimeFilter),)

    def _session_data(self, obj: Session):
        """Return decoded session content."""
        return obj.get_decoded()
