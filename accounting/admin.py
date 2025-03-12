from django.contrib import admin
from django.utils import timezone

from .models import UserAPIToken


@admin.register(UserAPIToken)
class CustomTokenAdmin(admin.ModelAdmin):
    list_display = ("verbose_info", "description", "created", "last_used", "expired")
    search_fields = ("user__username", "description")
    readonly_fields = ("key", "last_used")
    ordering = ("-created",)

    fieldsets = (
        (
            "Настройки",
            {"fields": ("user", "description", "expired", "last_used")},
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
