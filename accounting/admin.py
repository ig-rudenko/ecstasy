from django.contrib import admin
from django.contrib.admin.utils import quote
from django.contrib.admin.views.main import ChangeList
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from .models import UserAPIToken

User = get_user_model()


class TokenChangeList(ChangeList):
    """Map to matching User id"""

    def url_for_result(self, result):
        pk = result.user.pk
        return reverse(
            "admin:%s_%s_change" % (self.opts.app_label, self.opts.model_name),
            args=(quote(pk),),
            current_app=self.model_admin.admin_site.name,
        )


@admin.register(UserAPIToken)
class CustomTokenAdmin(admin.ModelAdmin):
    list_display = ("verbose_info", "description", "created", "last_used", "expired")
    search_fields = ("user__username", "description")
    readonly_fields = ("key", "last_used")
    ordering = ("-created",)
    actions = None  # Actions not compatible with mapped IDs.

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

    def get_changelist(self, request, **kwargs):
        return TokenChangeList

    def get_object(self, request, object_id, from_field=None):
        """
        Map from User ID to matching Token.
        """
        queryset = self.get_queryset(request)
        field = User._meta.pk
        try:
            object_id = field.to_python(object_id)
            user = User.objects.get(**{field.name: object_id})
            return queryset.get(user=user)
        except (queryset.model.DoesNotExist, User.DoesNotExist, ValidationError, ValueError):
            return None

    def delete_model(self, request, obj):
        # Map back to actual Token, since delete() uses pk.
        token = UserAPIToken.objects.get(key=obj.key)
        return super().delete_model(request, token)
