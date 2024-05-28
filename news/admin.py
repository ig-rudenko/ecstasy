from django.contrib import admin
from django.utils import timezone
from django.utils.safestring import mark_safe

from .models import GlobalNews


@admin.register(GlobalNews)
class GlobalNewsAdmin(admin.ModelAdmin):
    list_display = ("severity_title", "created_at", "expired_at")

    @admin.display(description="Заголовок")
    def severity_title(self, obj: GlobalNews) -> str:
        text = ""
        if obj.severity == "success":
            text = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="#198754" style="padding-right: 5px;" viewBox="0 0 16 16">
              <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0m-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"></path>
            </svg>"""
        elif obj.severity == "warning":
            text = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="#ffc107" style="padding-right: 5px;" viewBox="0 0 16 16">
              <path d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5m.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2"></path>
            </svg>"""
        elif obj.severity == "danger":
            text = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="#dc3545" style="padding-right: 5px;" viewBox="0 0 16 16">
              <path d="M11.46.146A.5.5 0 0 0 11.107 0H4.893a.5.5 0 0 0-.353.146L.146 4.54A.5.5 0 0 0 0 4.893v6.214a.5.5 0 0 0 .146.353l4.394 4.394a.5.5 0 0 0 .353.146h6.214a.5.5 0 0 0 .353-.146l4.394-4.394a.5.5 0 0 0 .146-.353V4.893a.5.5 0 0 0-.146-.353zM8 4c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995A.905.905 0 0 1 8 4m.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2"></path>
            </svg>"""
        elif obj.severity == "info":
            text = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="#0dcaf0" style="padding-right: 5px;" viewBox="0 0 16 16">
              <path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16m.93-9.412-1 4.705c-.07.34.029.533.304.533.194 0 .487-.07.686-.246l-.088.416c-.287.346-.92.598-1.465.598-.703 0-1.002-.422-.808-1.319l.738-3.468c.064-.293.006-.399-.287-.47l-.451-.081.082-.381 2.29-.287zM8 5.5a1 1 0 1 1 0-2 1 1 0 0 1 0 2"></path>
            </svg>"""

        is_expired = obj.expired_at is not None and obj.expired_at < timezone.now()

        text += f"<span style=\"color: {'red' if is_expired else 'currentColor'}\">{obj.title}</span>"

        if is_expired:
            text += f'<small style="color: red; margin-left: 5px;">(Срок действия сообщения истек)</small>'

        return mark_safe(text)
