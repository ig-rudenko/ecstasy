"""

## Админка для взаимодействия с оборудованием, создание нового, изменение

Добавление профилей авторизации к оборудованию, групп

Также управление профилем пользователя, уровнем привилегий

Переопределение пользователя с добавлением дополнительных полей

Также просмотр логов действий пользователей
"""
import orjson

from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from devicemanager.device import Interfaces
from net_tools.models import DevicesInfo
from .models import DeviceGroup, Devices, AuthGroup, Bras, Profile, UsersActions


@admin.register(DeviceGroup)
class DeviceGroupAdmin(admin.ModelAdmin):
    """Управление группами оборудования"""

    list_display = ["name", "description"]


@admin.register(Devices)
class DevicesAdmin(admin.ModelAdmin):
    """Управление оборудованием"""

    list_display = ["ip", "name", "vendor", "model", "group", "auth_group", "show_device"]
    list_filter = ["vendor", "group", "auth_group", "model"]
    search_fields = ["ip", "name"]
    readonly_fields = ["show_interfaces"]
    list_select_related = ["auth_group", "group"]
    list_per_page = 50

    fieldsets = (
        ("Характеристика", {"fields": ("ip", "name")}),
        ("Тип", {"fields": ("vendor", "model")}),
        ("Принадлежность", {"fields": ("group", "auth_group")}),
        (
            "Удаленное подключение",
            {"fields": ("snmp_community", "port_scan_protocol", "cmd_protocol")},
        ),
        ("Интерфейсы", {"fields": ("show_interfaces",)}),
    )
    actions = ["set_telnet", "set_snmp", "set_ssh"]

    @admin.display(description="Интерфейсы")
    def show_interfaces(self, obj: Devices):
        dev_info = DevicesInfo.objects.get(dev=obj)
        interfaces = (
            str(Interfaces(orjson.loads(dev_info.interfaces)))
            .replace("\n", "<br>")
            .replace(" ", "&nbsp; ")
        )
        return format_html(f"<div>{interfaces}</div>")

    @admin.display(description="Посмотреть")
    def show_device(self, obj: Devices):
        """Ссылка на страницу сканирования интерфейсов оборудования"""

        return mark_safe(
            f"""<a target="_blank" href="{obj.get_absolute_url()}">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-box-arrow-in-right" viewBox="0 0 16 16">
                  <path fill-rule="evenodd" d="M6 3.5a.5.5 0 0 1 .5-.5h8a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5h-8a.5.5 0 0 1-.5-.5v-2a.5.5 0 0 0-1 0v2A1.5 1.5 0 0 0 6.5 14h8a1.5 1.5 0 0 0 1.5-1.5v-9A1.5 1.5 0 0 0 14.5 2h-8A1.5 1.5 0 0 0 5 3.5v2a.5.5 0 0 0 1 0v-2z"/>
                  <path fill-rule="evenodd" d="M11.854 8.354a.5.5 0 0 0 0-.708l-3-3a.5.5 0 1 0-.708.708L10.293 7.5H1.5a.5.5 0 0 0 0 1h8.793l-2.147 2.146a.5.5 0 0 0 .708.708l3-3z"/>
                </svg>
            </a>"""
        )

    @admin.action(description="telnet Протокол для поиска интерфейсов")
    def set_telnet(self, request, queryset):
        """Действие. Меняем протокол поиска интерфейсов на TELNET"""

        queryset.update(port_scan_protocol="telnet")

    @admin.action(description="snmp Протокол для поиска интерфейсов")
    def set_snmp(self, request, queryset):
        """Действие. Меняем протокол поиска интерфейсов на SNMP"""

        queryset.update(port_scan_protocol="snmp")

    @admin.action(description="ssh Протокол для поиска интерфейсов")
    def set_ssh(self, request, queryset):
        """Действие. Меняем протокол поиска интерфейсов на SSH"""

        queryset.update(port_scan_protocol="ssh")


@admin.register(AuthGroup)
class AuthGroupAdmin(admin.ModelAdmin):
    """Взаимодействие с профилями авторизации к оборудованию"""

    list_display = ["name", "login", "description"]
    search_fields = ["name", "login"]


@admin.register(Bras)
class BrasAdmin(admin.ModelAdmin):
    """Настройка для маршрутизаторов широкополосного удалённого доступа BRAS"""

    list_display = ["name", "ip"]
    search_fields = ["name", "ip"]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Управление уровнем привилегий пользователей"""

    list_display = ["user", "permissions"]

    @admin.display(description="Пользователь")
    def user(self, obj: Profile):
        """Отображаем username пользователя"""

        return obj.user.username


admin.site.unregister(User)  # Отменяем старую админку для пользователя


@admin.register(User)
class UserProfileAdmin(UserAdmin):
    """Переопределенный класс для пользователя"""

    list_display = [
        "username",
        "first_name",
        "last_name",
        "email",
        "is_active",
        "is_superuser",
        "last_login",
        "permission",
        "dev_groups",
    ]

    @admin.display(description="Права")
    def permission(self, obj: User):
        """Отображение привилегий пользователя"""

        return Profile.objects.get(user_id=obj.pk).permissions

    @admin.display(description="Группы")
    def dev_groups(self, obj: User):
        """Отображение доступных групп для пользователя"""

        groups_string = ""
        for group in obj.profile.devices_groups.all():
            groups_string += f"<li>{group}</li>"
        return mark_safe(groups_string)


@admin.register(UsersActions)
class UsersActionsAdmin(admin.ModelAdmin):
    """Просмотр логов действий пользователя"""

    list_display = ["time", "user", "device", "action"]
    list_filter = ["user"]
    search_fields = ["action"]
    readonly_fields = list_display
    list_per_page = 50
