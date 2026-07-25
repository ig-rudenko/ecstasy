from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import RangeDateTimeFilter
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from apps.check.models import Profile

from .models import User, UserAPIToken


@admin.register(User)
class UserProfileAdmin(BaseUserAdmin):
    """Переопределенный класс для пользователя"""

    list_display = [
        "username",
        "verbose_name",
        "email",
        "is_active",
        "last_login",
        "permission",
        "dev_groups",
    ]

    @admin.display(description="")
    def verbose_name(self, obj: User):
        return f"{obj.first_name} {obj.last_name}"

    @admin.display(description="Права")
    def permission(self, obj: User):
        """Отображение привилегий пользователя"""
        return ", ".join(
            permission.split(".", 1)[1] for permission in sorted(Profile.get_user_device_permissions(obj))
        )

    @admin.display(description="Группы")
    def dev_groups(self, obj: User):
        """Отображение доступных групп для пользователя"""
        try:
            profile: Profile = Profile.objects.get(user=obj)
        except Profile.DoesNotExist:
            return ""

        user_groups = profile.devices_groups.all()
        groups_string = "".join([f"<li>{group}</li>" for group in user_groups])
        return mark_safe(groups_string)


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


admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    # Forms loaded from `unfold.forms`
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass
