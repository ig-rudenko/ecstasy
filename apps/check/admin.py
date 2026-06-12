"""

## Админка для взаимодействия с оборудованием, создание нового, изменение

Добавление профилей авторизации к оборудованию, групп

Также управление профилем пользователя, уровнем привилегий

Переопределение пользователя с добавлением дополнительных полей

Также просмотр логов действий пользователей
"""

# pylint: disable=maybe-no-member
import zipfile
from datetime import datetime

import orjson
from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db.models import Count, QuerySet
from django.http import HttpResponse
from django.utils.html import format_html, format_html_join, linebreaks
from django.utils.safestring import mark_safe
from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    ChoicesDropdownFilter,
    MultipleRelatedDropdownFilter,
    RangeDateTimeFilter,
    RelatedDropdownFilter,
)
from unfold.contrib.import_export.forms import ImportForm, SelectableFieldsExportForm
from unfold.widgets import UnfoldAdminSelectWidget, UnfoldAdminTextareaWidget

from apps.gathering.services.configurations import LocalConfigStorage
from devicemanager.device import Interfaces
from ecstasy_project.admin_filters import distinct_dropdown_filter

from .export import DevicesInterfacesWorkloadExcelExport
from .export_resources import DevicesResource
from .models import (
    AccessGroup,
    AuthGroup,
    Bras,
    BulkDeviceCommandExecution,
    BulkDeviceCommandExecutionResult,
    DeviceCommand,
    DeviceGroup,
    DeviceInterfacePatternRule,
    DeviceMedia,
    Devices,
    InterfacesComments,
    Profile,
    UsersActions,
)
from .services.device.commands import CommandMacro, iter_command_macros, validate_command_template


class BulkDeviceCommandExecutionResultInline(TabularInline):
    """Inline results for one bulk command execution."""

    model = BulkDeviceCommandExecutionResult
    extra = 0
    tab = True
    can_delete = False
    readonly_fields = (
        "device",
        "device_name",
        "status",
        "command_text",
        "output",
        "detail",
        "error",
        "duration",
        "created_at",
        "updated_at",
    )
    fields = readonly_fields


class ProfileInline(TabularInline):
    model = Profile.devices_groups.through
    tab = True


VendorDropdownFilter = distinct_dropdown_filter("vendor", "vendor")
ModelDropdownFilter = distinct_dropdown_filter("model", "model")
ConnectionPoolSizeDropdownFilter = distinct_dropdown_filter("connection_pool_size", "connection pool size")
DeviceVendorDropdownFilter = distinct_dropdown_filter("device_vendor", "device vendor")
InterfacePatternVendorDropdownFilter = distinct_dropdown_filter("vendor", "vendor")


@admin.register(DeviceInterfacePatternRule)
class DeviceInterfacePatternRuleAdmin(ModelAdmin):
    """Управление общими паттернами интерфейсов по производителю и модели."""

    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = True
    list_display = [
        "name",
        "enabled",
        "vendor",
        "model_match_type",
        "model_pattern",
        "interface_pattern",
        "priority",
        "matched_devices_count",
        "updated_at",
    ]
    list_filter = [
        "enabled",
        InterfacePatternVendorDropdownFilter,
        ("model_match_type", ChoicesDropdownFilter),
    ]
    search_fields = ["name", "vendor", "model_pattern", "interface_pattern", "description"]
    readonly_fields = ["matched_devices_count", "created_at", "updated_at"]
    ordering = ["vendor", "model_pattern", "-priority", "id"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "enabled",
                    "name",
                    "vendor",
                    "model_match_type",
                    "model_pattern",
                    "interface_pattern",
                    "priority",
                    "description",
                )
            },
        ),
        (
            "Служебная информация",
            {"fields": ("matched_devices_count", "created_at", "updated_at")},
        ),
    )

    @admin.display(description="Подходит устройств")
    def matched_devices_count(self, obj: DeviceInterfacePatternRule) -> int:
        """Return number of devices matched by this rule."""
        devices = Devices.objects.filter(vendor__iexact=obj.vendor.strip()).only("vendor", "model")
        return sum(1 for device in devices if obj.matches_device(device))


@admin.register(DeviceGroup)
class DeviceGroupAdmin(ModelAdmin):
    """Управление группами оборудования"""

    compressed_fields = True
    warn_unsaved_form = True
    list_display = ["name", "description", "dev_count"]
    search_fields = ["name", "description"]
    inlines = [ProfileInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(dev_count=Count("devices"))

    @admin.display(description="Кол-во")
    def dev_count(self, obj) -> int:
        return obj.dev_count


@admin.register(Devices)
class DevicesAdmin(ModelAdmin, ImportExportModelAdmin):
    """Управление оборудованием"""

    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm

    resource_class = DevicesResource
    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = True

    list_display = [
        "show_ip_address",
        "show_name",
        "show_vendor",
        "show_model",
        "show_group",
        "show_auth_group",
        "show_auth_type",
        "show_device",
    ]
    list_filter = [
        ("group", RelatedDropdownFilter),
        ("auth_group", RelatedDropdownFilter),
        VendorDropdownFilter,
        ModelDropdownFilter,
        ("port_scan_protocol", ChoicesDropdownFilter),
        ("cmd_protocol", ChoicesDropdownFilter),
        ConnectionPoolSizeDropdownFilter,
        "active",
        "collect_interfaces",
        "collect_mac_addresses",
        "collect_vlan_info",
        "collect_configurations",
    ]
    radio_fields = {
        "port_scan_protocol": admin.HORIZONTAL,
        "cmd_protocol": admin.HORIZONTAL,
    }
    readonly_fields = ["show_interfaces", "show_interfaces_vlans"]
    search_fields = ["ip", "name"]
    list_select_related = ["auth_group", "group"]
    list_per_page = 50

    fieldsets = (
        (
            "Характеристика",
            {
                "fields": ("name", "ip", "active"),
                "classes": ("tab", "wide"),
            },
        ),
        (
            "Данные",
            {
                "fields": ("vendor", "model", "serial_number", "os_version", "latitude", "longitude"),
                "classes": ("tab",),
            },
        ),
        (
            "Принадлежность",
            {"fields": ("group", "auth_group"), "classes": ("tab",)},
        ),
        (
            "Удаленное подключение",
            {
                "classes": ("tab",),
                "fields": (
                    "snmp_community",
                    "port_scan_protocol",
                    "cmd_protocol",
                    "telnet_port",
                    "ssh_port",
                    "snmp_port",
                    "connection_pool_size",
                ),
            },
        ),
        (
            "Периодические опросы",
            {
                "fields": (
                    "collect_interfaces",
                    "collect_mac_addresses",
                    "collect_vlan_info",
                    "collect_configurations",
                ),
                "classes": ("tab",),
            },
        ),
        (
            "Интерфейсы",
            {"fields": ("interface_pattern", "show_interfaces"), "classes": ("tab",)},
        ),
        (
            "VLANS",
            {"fields": ("show_interfaces_vlans",), "classes": ("tab",)},
        ),
    )
    actions = [
        "activate_devices",
        "deactivate_devices",
        "excel_interfaces_export",
        "load_last_config_files",
        "set_telnet_port_scan_protocol",
        "set_snmp_port_scan_protocol",
        "set_ssh_port_scan_protocol",
        "set_telnet_cmd_protocol",
        "set_ssh_cmd_protocol",
        "set_pool_size_1",
        "set_pool_size_2",
        "set_pool_size_3",
        "set_pool_size_4",
        "disable_interface_collector",
        "enable_interface_collector",
        "disable_mac_collector",
        "enable_mac_collector",
        "disable_vlan_collector",
        "enable_vlan_collector",
        "disable_configuration_collector",
        "enable_configuration_collector",
        "sync_coordinates_with_zabbix",
    ]
    autocomplete_fields = ("auth_group", "group")

    @admin.display(description="IP-адрес")
    def show_ip_address(self, obj: Devices):
        active = "" if obj.active else "❌"
        return mark_safe(f"""<span style="font-family: monospace;">{active} {obj.ip}</span>""")

    @admin.display(description="Название")
    def show_name(self, obj: Devices):
        return mark_safe(f"""<span style="font-family: monospace;">{obj.name}</span>""")

    @admin.display(description="Производитель")
    def show_vendor(self, obj: Devices):
        return mark_safe(f"""<span style="font-family: monospace;">{obj.vendor}</span>""")

    @admin.display(description="Модель")
    def show_model(self, obj: Devices):
        return mark_safe(f"""<span style="font-family: monospace;">{obj.model}</span>""")

    @admin.display(description="Группа")
    def show_group(self, obj: Devices):
        return mark_safe(f"""<span style="font-family: monospace;">{obj.group.name}</span>""")

    @admin.display(description="Авторизация")
    def show_auth_group(self, obj: Devices):
        return mark_safe(f"""<span style="font-family: monospace;">{obj.auth_group.name}</span>""")

    @admin.display(description="Тип подключения")
    def show_auth_type(self, obj: Devices):
        text = ""
        if obj.port_scan_protocol == "telnet":
            text += "TELNET ❗️"
        elif obj.port_scan_protocol == "ssh":
            text += "SSH ✅"
        elif obj.port_scan_protocol == "snmp":
            text += "SNMP"

        if obj.cmd_protocol != obj.port_scan_protocol:
            if obj.cmd_protocol == "telnet":
                text += " + TELNET ❗️"
            elif obj.cmd_protocol == "ssh":
                text += "+ SSH ✅"

        return mark_safe(text)

    @admin.display(description="Интерфейсы")
    def show_interfaces(self, obj: Devices):
        """Выводит табличку интерфейсов оборудования из истории"""
        interfaces = str(Interfaces(orjson.loads(obj.devicesinfo.interfaces or "[]")))
        return mark_safe(f"""
            <div style"overflow-x: scroll;">
                <div style="font-family: monospace; white-space: pre;">{interfaces}</div>
            </div>""")

    @admin.display(description="Интерфейсы & VLANS")
    def show_interfaces_vlans(self, obj: Devices):
        """Выводит табличку интерфейсов оборудования из истории"""
        interfaces = str(Interfaces(orjson.loads(obj.devicesinfo.vlans or "[]")))
        return mark_safe(f"""
            <div style"overflow-x: scroll;">
                <div style="font-family: monospace; white-space: pre;">{interfaces}</div>
            </div>""")

    @admin.display(description="Посмотреть")
    def show_device(self, obj: Devices):
        """Ссылка на страницу сканирования интерфейсов оборудования"""

        return mark_safe(f"""<a target="_blank" href="{obj.get_absolute_url()}">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" 
                class="bi bi-box-arrow-in-right" viewBox="0 0 16 16">
                  <path fill-rule="evenodd" d="M6 3.5a.5.5 0 0 1 .5-.5h8a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5h-8a.5.5 
                  0 0 1-.5-.5v-2a.5.5 0 0 0-1 0v2A1.5 1.5 0 0 0 6.5 14h8a1.5 1.5 0 0 0 1.5-1.5v-9A1.5 1.5 0 0 0 14.5 
                  2h-8A1.5 1.5 0 0 0 5 3.5v2a.5.5 0 0 0 1 0v-2z"/>
                  <path fill-rule="evenodd" d="M11.854 8.354a.5.5 0 0 0 0-.708l-3-3a.5.5 0 1 0-.708.708L10.293 
                  7.5H1.5a.5.5 0 0 0 0 1h8.793l-2.147 2.146a.5.5 0 0 0 .708.708l3-3z"/>
                </svg>
            </a>""")

    @admin.action(description="✅ Активировать")
    def activate_devices(self, request, queryset):
        queryset.update(active=True)

    @admin.action(description="🚫 Деактивировать")
    def deactivate_devices(self, request, queryset):
        queryset.update(active=False)

    @admin.action(description="🔓 telnet Протокол для поиска интерфейсов")
    def set_telnet_port_scan_protocol(self, request, queryset):
        queryset.update(port_scan_protocol="telnet")

    @admin.action(description="🔎 snmp Протокол для поиска интерфейсов")
    def set_snmp_port_scan_protocol(self, request, queryset):
        queryset.update(port_scan_protocol="snmp")

    @admin.action(description="🔐 ssh Протокол для поиска интерфейсов")
    def set_ssh_port_scan_protocol(self, request, queryset):
        queryset.update(port_scan_protocol="ssh")

    @admin.action(description="🔓 telnet Протокол для подключения")
    def set_telnet_cmd_protocol(self, request, queryset):
        queryset.update(cmd_protocol="telnet")

    @admin.action(description="🔐 ssh Протокол для подключения")
    def set_ssh_cmd_protocol(self, request, queryset):
        queryset.update(cmd_protocol="ssh")

    @admin.action(description="📶 Установка пула подключений в 1")
    def set_pool_size_1(self, request, queryset):
        queryset.update(connection_pool_size=1)

    @admin.action(description="📶 Установка пула подключений в 2")
    def set_pool_size_2(self, request, queryset):
        queryset.update(connection_pool_size=3)

    @admin.action(description="📶 Установка пула подключений в 3")
    def set_pool_size_3(self, request, queryset):
        queryset.update(connection_pool_size=3)

    @admin.action(description="📶 Установка пула подключений в 4")
    def set_pool_size_4(self, request, queryset):
        queryset.update(connection_pool_size=4)

    @admin.action(description="📊 Экспорт ёмкости интерфейсов в xls")
    def excel_interfaces_export(self, request, queryset):
        """Экспортируем ёмкость интерфейсов в excel файл"""
        export = DevicesInterfacesWorkloadExcelExport(queryset)
        export.make_excel()
        return export.create_response()

    @admin.action(description="❌ Отключить сбор интерфейсов")
    def disable_interface_collector(self, request, queryset):
        queryset.update(collect_interfaces=False)

    @admin.action(description="❌ Отключить сбор MAC")
    def disable_mac_collector(self, request, queryset):
        queryset.update(collect_mac_addresses=False)

    @admin.action(description="❌ Отключить сбор интерфейсов")
    def disable_vlan_collector(self, request, queryset):
        queryset.update(collect_vlan_info=False)

    @admin.action(description="❌ Отключить сбор интерфейсов")
    def disable_configuration_collector(self, request, queryset):
        queryset.update(collect_configurations=False)

    @admin.action(description="✅ Включить сбор интерфейсов")
    def enable_interface_collector(self, request, queryset):
        queryset.update(collect_interfaces=True)

    @admin.action(description="✅ Включить сбор MAC")
    def enable_mac_collector(self, request, queryset):
        queryset.update(collect_mac_addresses=True)

    @admin.action(description="✅ Включить сбор интерфейсов")
    def enable_vlan_collector(self, request, queryset):
        queryset.update(collect_vlan_info=True)

    @admin.action(description="✅ Включить сбор интерфейсов")
    def enable_configuration_collector(self, request, queryset):
        queryset.update(collect_configurations=True)

    @admin.action(description="Синхронизировать координаты с Zabbix")
    def sync_coordinates_with_zabbix(self, request, queryset: QuerySet[Devices]):
        """Start coordinate synchronization for selected devices."""
        from apps.check.tasks import sync_device_coordinates_with_zabbix_task

        device_ids = list(queryset.values_list("id", flat=True))
        sync_device_coordinates_with_zabbix_task.delay(device_ids=device_ids)
        self.message_user(request, f"Запущена синхронизация координат для устройств: {len(device_ids)}")

    @admin.action(description="📦 Скачать последние конфигурации ZIP")
    def load_last_config_files(self, request, queryset: QuerySet[Devices]):
        """
        Функция `load_last_config_files` создает zip-файл, содержащий первый файл конфигурации с каждого устройства в
        заданном наборе запросов, и возвращает его как загружаемый ответ.

        :return: Код возвращает объект HttpResponse с вложенным zip-файлом.
        """
        config_files_path_list = []
        for device in queryset:
            storage = LocalConfigStorage(device)
            configs = storage.files_list()
            if configs:
                config_files_path_list.append(configs[0].path)

        archive_storage_dir = settings.CONFIG_STORAGE_DIR / "archives"
        archive_storage_dir.mkdir(parents=True, exist_ok=True)

        datetime_part = datetime.now().strftime("%d %b %Y %Hh %Mm")

        zip_file_path = archive_storage_dir / f"devices_({len(config_files_path_list)})_{datetime_part}.zip"

        with zipfile.ZipFile(zip_file_path, "w") as my_zip:
            for file in config_files_path_list:
                if isinstance(file, str):
                    file_path = file
                else:
                    file_path = str(file.absolute().as_posix())

                file_name_with_parent_folder = file_path.split("/")[-2:]
                my_zip.write(filename=file, arcname="/".join(file_name_with_parent_folder))

        response = HttpResponse(zip_file_path.open("rb"), content_type="application/x-zip-compressed")
        response["Content-Disposition"] = f"attachment; filename={zip_file_path.name}"
        zip_file_path.unlink()
        return response


@admin.register(AuthGroup)
class AuthGroupAdmin(ModelAdmin):
    """Взаимодействие с профилями авторизации к оборудованию"""

    compressed_fields = True
    warn_unsaved_form = True
    list_display = ["name", "login", "description", "dev_count"]
    search_fields = ["name", "login"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(dev_count=Count("devices"))

    @admin.display(description="Кол-во")
    def dev_count(self, obj) -> int:
        return obj.dev_count


@admin.register(Bras)
class BrasAdmin(ModelAdmin):
    """Настройка для маршрутизаторов широкополосного удалённого доступа BRAS"""

    compressed_fields = True
    warn_unsaved_form = True
    list_display = ["device", "device_ip"]
    list_select_related = ["device"]
    search_fields = ["device__name", "device__ip"]

    @admin.display(description="IP адрес", ordering="device__ip")
    def device_ip(self, obj: Bras) -> str:
        """Вернуть IP-адрес связанного оборудования."""
        return obj.device.ip


@admin.register(Profile)
class ProfileAdmin(ModelAdmin):
    """Управление уровнем привилегий пользователей"""

    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = True
    list_display = ["user", "permissions", "user_is_active", "dev_groups", "console_access"]
    list_select_related = ["user"]
    filter_horizontal = ["devices_groups"]
    list_filter = [
        ("permissions", ChoicesDropdownFilter),
        ("devices_groups", MultipleRelatedDropdownFilter),
        "console_access",
        "user__is_active",
        "user__is_staff",
    ]
    search_fields = ("user__username", "user__first_name", "user__last_name", "user__email")
    autocomplete_fields = ("user",)

    @admin.display(description="Пользователь")
    def user(self, obj: Profile):
        return obj.user.username

    @admin.display(description="Активный", boolean=True)
    def user_is_active(self, obj: Profile):
        return obj.user.is_active

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("devices_groups")

    @admin.display(description="Группы")
    def dev_groups(self, obj: Profile):
        """Отображение доступных групп для пользователя"""
        user_groups = obj.devices_groups.all()
        groups_string = "".join([f"<li>{group.name}</li>" for group in user_groups])  # noqa
        return mark_safe(groups_string)


admin.site.unregister(User)  # Отменяем старую админку для пользователя


@admin.register(User)
class UserProfileAdmin(UserAdmin):
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
        return Profile.objects.get(user_id=obj.pk).permissions

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


@admin.register(UsersActions)
class UsersActionsAdmin(ModelAdmin):
    """Просмотр логов действий пользователя"""

    list_filter_submit = True
    list_display = ["time", "user", "device", "action"]
    list_filter = [
        ("time", RangeDateTimeFilter),
        ("user", RelatedDropdownFilter),
        ("device", RelatedDropdownFilter),
    ]
    search_fields = ["action"]
    date_hierarchy = "time"
    readonly_fields = ["time", "user", "device", "action"]
    list_per_page = 25
    list_select_related = ["device", "user"]


@admin.register(BulkDeviceCommandExecution)
class BulkDeviceCommandExecutionAdmin(ModelAdmin):
    """Browse persisted bulk command history."""

    list_filter_submit = True
    list_display = (
        "launched_at",
        "user",
        "command_name",
        "verbose_status",
        "progress_percentage",
        "processed",
        "total",
    )
    list_filter = (
        ("launched_at", RangeDateTimeFilter),
        ("user", RelatedDropdownFilter),
        "status",
    )
    search_fields = ("task_id", "command_name", "command_body", "user__username")
    list_select_related = ("user", "command")
    readonly_fields = (
        "task_id",
        "user",
        "command",
        "command_name",
        "command_body",
        "context",
        "status",
        "verbose_status",
        "progress",
        "progress_percentage",
        "processed",
        "total",
        "launched_at",
        "finished_at",
        "verbose_command_name",
        "verbose_command_body",
    )
    inlines = [BulkDeviceCommandExecutionResultInline]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "task_id",
                    "verbose_status",
                    "progress_percentage",
                    "user",
                    "verbose_command_name",
                    "verbose_command_body",
                    "context",
                    "processed",
                    "total",
                    "launched_at",
                    "finished_at",
                )
            },
        ),
    )

    @admin.display(description="command name")
    def verbose_command_name(self, obj: BulkDeviceCommandExecution) -> str:
        return mark_safe(f"<div style='font-family: monospace'>{obj.command_name}</div>")

    @admin.display(description="command")
    def verbose_command_body(self, obj: BulkDeviceCommandExecution) -> str:
        return mark_safe(f"<div style='font-family: monospace'>{obj.command_body}</div>")

    @admin.display(description="status")
    def verbose_status(self, obj: BulkDeviceCommandExecution) -> str:
        if obj.status == obj.STATUS_SUCCESS:
            return f"✅ {obj.status}"
        if obj.status == obj.STATUS_FAILURE:
            return f"❌ {obj.status}"
        if obj.status == obj.STATUS_PROGRESS:
            return f"🔄 {obj.status}"
        if obj.status == obj.STATUS_REVOKED:
            return f"⏩ {obj.status}"
        return f"{obj.status}"

    @admin.display(description="progress_percentage")
    def progress_percentage(self, obj: BulkDeviceCommandExecution) -> str:
        return f"{obj.progress}%"


@admin.register(BulkDeviceCommandExecutionResult)
class BulkDeviceCommandExecutionResultAdmin(ModelAdmin):
    """Browse persisted per-device bulk command results."""

    list_filter_submit = True
    list_display = (
        "created_at",
        "execution",
        "device_name",
        "duration",
        "verbose_status",
    )
    list_filter = (
        ("created_at", RangeDateTimeFilter),
        ("device", RelatedDropdownFilter),
        "status",
    )
    search_fields = ("device_name", "command_text", "output", "detail", "error", "execution__task_id")
    list_select_related = ("execution", "device", "execution__user")
    readonly_fields = (
        "execution",
        "duration",
        "device",
        "device_name",
        "status",
        "created_at",
        "updated_at",
        "command_text",
        "verbose_output",
        "error",
        "detail",
    )
    fieldsets = (
        (
            None,
            {"fields": ("execution", "duration", "device", "status", "created_at", "updated_at")},
        ),
        (
            "Command",
            {"fields": ("command_text", "verbose_output")},
        ),
        (
            "Errors",
            {"fields": ("error", "detail")},
        ),
    )

    @admin.display(description="output")
    def verbose_output(self, obj: BulkDeviceCommandExecutionResult) -> str:
        return mark_safe(f'<div style="font-family: monospace">{linebreaks(obj.output)}</div>')

    @admin.display(description="status")
    def verbose_status(self, obj: BulkDeviceCommandExecutionResult) -> str:
        if obj.status == obj.STATUS_SUCCESS:
            return f"✅ {obj.status}"
        if obj.status == obj.STATUS_ERROR:
            return f"❌ {obj.status}"
        if obj.status == obj.STATUS_RUNNING:
            return f"🔄 {obj.status}"
        if obj.status == obj.STATUS_SKIPPED:
            return f"⏩ {obj.status}"
        return f"{obj.status}"


@admin.register(DeviceMedia)
class DeviceMediaAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_display = ["file_type", "file_name", "current_file"]
    search_fields = ["device__name"]
    list_select_related = ["device"]

    fieldsets = (
        (
            None,
            {"fields": ("description", "device", "file", "current_file")},
        ),
    )

    readonly_fields = ["current_file"]
    autocomplete_fields = ["device"]

    @admin.display(description="Тип")
    def file_type(self, obj: DeviceMedia) -> str:
        if obj.is_image:
            type_ = "image"
        else:
            type_ = obj.file_type
        return mark_safe(
            f'<i class="nav-icon fas fa-file-{type_}" style="font-size: 2rem; vertical-align: middle;"></i> {type_}'
        )

    @admin.display(description="Имя файла")
    def file_name(self, obj: DeviceMedia) -> str:
        return str(obj.file.name)

    @staticmethod
    def current_file(obj: DeviceMedia) -> str:
        if obj.is_image:
            return mark_safe(f'<img src="{obj.file.url}" style="max-height: 300px;" >')

        if obj.file_type == "pdf":
            return mark_safe(
                f"""<a href="{obj.file.url}"><svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" 
                fill="currentColor" class="bi bi-file-earmark-pdf" viewBox="0 0 16 16">
                      <path d="M14 14V4.5L9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2zM9.5 
                      3A1.5 1.5 0 0 0 11 4.5h2V14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h5.5v2z"/>
                      <path d="M4.603 14.087a.81.81 0 0 
                      1-.438-.42c-.195-.388-.13-.776.08-1.102.198-.307.526-.568.897-.787a7.68 7.68 0 0 1 1.482-.645
                       19.697 19.697 0 0 0 1.062-2.227 7.269 7.269 0 0 
                       1-.43-1.295c-.086-.4-.119-.796-.046-1.136.075-.354.274-.672.65-.823.192-.077.4-.12.602-.077a.7.7 
                       0 0 1 .477.365c.088.164.12.356.127.538.007.188-.012.396-.047.614-.084.51-.27 1.134-.52 
                       1.794a10.954 10.954 0 0 0 .98 1.686 5.753 5.753 0 0 1 
                       1.334.05c.364.066.734.195.96.465.12.144.193.32.2.518.007.192-.047.382-.138.563a1.04 1.04 0 0 
                       1-.354.416.856.856 0 0 1-.51.138c-.331-.014-.654-.196-.933-.417a5.712 5.712 0 0 1-.911-.95 
                       11.651 11.651 0 0 0-1.997.406 11.307 11.307 0 0 1-1.02 1.51c-.292.35-.609.656-.927.787a.793.793 
                       0 0 1-.58.029zm1.379-1.901c-.166.076-.32.156-.459.238-.328.194-.541.383-.647.547-
                       .094.145-.096.25-.04.361.01.022.02.036.026.044a.266.266 0 0 0 .035-.012c.137-.056.355-
                       .235.635-.572a8.18 8.18 0 0 0 .45-.606zm1.64-1.33a12.71 12.71 0 0 1 1.01-.193 11.744 
                       11.744 0 0 1-.51-.858 20.801 20.801 0 0 1-.5 1.05zm2.446.45c.15.163.296.3.435.41.24.19.407
                       .253.498.256a.107.107 0 0 0 .07-.015.307.307 0 0 0 .094-.125.436.436 0 0 0 .059-.2.095.095 
                       0 0 0-.026-.063c-.052-.062-.2-.152-.518-.209a3.876 3.876 0 0 0-.612-.053zM8.078 7.8a6.7 6.7 
                       0 0 0 .2-.828c.031-.188.043-.343.038-.465a.613.613 0 0 0-.032-.198.517.517 0 0 0-.145.04c
                       -.087.035-.158.106-.196.283-.04.192-.03.469.046.822.024.111.054.227.09.346z"/>
                    </svg></a>"""
            )

        return ""


COMMAND_MACRO_LABELS = {
    "ip": "IP-адрес",
    "port": "Порт оборудования",
    "mac": "MAC-адрес",
    "number": "Целое число",
    "word": "Слово без пробелов",
}
COMMAND_MACRO_STYLE = (
    "color: #1d4ed8; background-color: rgba(37, 99, 235, 0.12); "
    "border: 1px solid rgba(37, 99, 235, 0.35); border-radius: 0.25rem; "
    "cursor: help; padding: 0.05rem 0.2rem;"
)
COMMAND_IF_MACRO_STYLE = (
    "color: #b45309; background-color: rgba(245, 158, 11, 0.15); "
    "border: 1px solid rgba(245, 158, 11, 0.45); border-radius: 0.25rem; "
    "cursor: help; padding: 0.05rem 0.2rem;"
)


def command_macro_description(macro: CommandMacro) -> str:
    """Return a detailed tooltip for one command macro."""
    if macro.kind == "if":
        return (
            "Условный макрос: после отправки команды ожидать регулярное выражение "
            f"«{macro.condition}», затем отправить ответ «{macro.response}»."
        )

    description = COMMAND_MACRO_LABELS[macro.kind]
    if macro.name:
        description += f". Имя параметра: «{macro.name}»"
    else:
        description += ". Используется значение параметра без имени"

    if macro.kind == "number":
        if macro.min_value is not None and macro.max_value is not None:
            description += f". Допустимый диапазон: от {macro.min_value} до {macro.max_value}"
        elif macro.min_value is not None:
            description += f". Минимальное значение: {macro.min_value}"
        elif macro.max_value is not None:
            description += f". Максимальное значение: {macro.max_value}"

    return description + "."


def command_macro_name_styles(command: str) -> dict[str, str]:
    """Assign a distinct color to each macro parameter name."""
    names = dict.fromkeys(macro.name for macro in iter_command_macros(command) if macro.name)
    styles = {}

    for index, name in enumerate(names):
        hue = round((210 + index * 137.508) % 360)
        styles[name] = (
            f"color: hsl({hue}, 75%, 32%); background-color: hsl({hue}, 85%, 90%); "
            "border-radius: 0.2rem; font-weight: 700; padding: 0 0.1rem;"
        )

    return styles


def render_command_macro(macro: CommandMacro, name_styles: dict[str, str]):
    """Render one command macro with highlighting and a tooltip."""
    macro_class = "device-command-macro"
    macro_style = COMMAND_MACRO_STYLE
    if macro.kind == "if":
        macro_class += " device-command-macro-if"
        macro_style = COMMAND_IF_MACRO_STYLE

    macro_content = format_html("{}", macro.text)
    if macro.name and macro.name_start is not None and macro.name_end is not None:
        name_start = macro.name_start - macro.start
        name_end = macro.name_end - macro.start
        macro_content = format_html(
            '{}<span class="device-command-macro-name" style="{}">{}</span>{}',
            macro.text[:name_start],
            name_styles[macro.name],
            macro.name,
            macro.text[name_end:],
        )

    description = command_macro_description(macro)
    return format_html(
        '<span class="{}" style="{}" title="{}" aria-label="{}">{}</span>',
        macro_class,
        macro_style,
        description,
        description,
        macro_content,
    )


def render_command_line(command_line: str, name_styles: dict[str, str]):
    """Render one command line and add a detailed macro summary tooltip."""
    macros = list(iter_command_macros(command_line))
    fragments = []
    position = 0

    for macro in macros:
        fragments.append(format_html("{}", command_line[position : macro.start]))
        fragments.append(render_command_macro(macro, name_styles))
        position = macro.end

    fragments.append(format_html("{}", command_line[position:]))
    line_html = format_html_join("", "{}", ((fragment,) for fragment in fragments))
    if not command_line:
        line_html = format_html("&nbsp;")

    if not macros:
        return format_html(
            '<span class="device-command-line" style="display: inline-block; min-width: 100%;">{}</span>',
            line_html,
        )

    tooltip = "\n".join(
        f"{index}. {command_macro_description(macro)}" for index, macro in enumerate(macros, start=1)
    )
    return format_html(
        '<span class="device-command-line" style="cursor: help; display: inline-block; min-width: 100%;" '
        'title="{}" aria-label="{}">{}</span>',
        tooltip,
        tooltip,
        line_html,
    )


class DeviceCommandModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uniq_vendors = list(sorted(set(Devices.objects.all().values_list("vendor", flat=True)), key=str))
        self.fields["device_vendor"].widget = UnfoldAdminSelectWidget(choices=[(v, v) for v in uniq_vendors])

    def clean_command(self) -> str:
        """Validate command macros before saving the template."""
        command = self.cleaned_data["command"]
        validate_command_template(command)
        return command

    class Meta:
        model = DeviceCommand
        fields = [
            "name",
            "description",
            "command",
            "device_vendor",
            "model_regexp",
            "valid_regexp",
            "perm_groups",
        ]
        widgets = {
            "command": UnfoldAdminTextareaWidget(
                attrs={
                    "rows": 10,
                    "style": "font-family: monospace; font-size: 1rem; padding: 1rem; min-width: 100%;",
                    "wrap": "off",
                },
            ),
        }


@admin.register(DeviceCommand)
class DeviceCommandAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_display = ["name", "device_vendor", "model_regexp", "command_html", "description"]
    search_fields = ["name", "command"]
    filter_horizontal = ("perm_groups",)
    form = DeviceCommandModelForm
    list_filter = [DeviceVendorDropdownFilter]

    @admin.display(description="Команда", ordering="command")
    def command_html(self, obj):
        name_styles = command_macro_name_styles(obj.command)
        rendered_lines = [
            render_command_line(command_line, name_styles) for command_line in obj.command.split("\n")
        ]
        command_html = mark_safe("<br>".join(str(line) for line in rendered_lines))
        return format_html(
            '<code style="font-family: monospace; white-space: nowrap;">{}</code>',
            command_html,
        )


@admin.register(AccessGroup)
class AccessGroupAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = True
    list_display = (
        "name",
        "description_short",
        "devices_count",
        "forbidden_devices_count",
        "users_count",
        "created_at",
    )
    search_fields = ("name", "description")
    ordering = ("-created_at",)
    filter_horizontal = ("devices", "forbidden_devices", "users", "user_groups")
    list_filter = (
        ("users", MultipleRelatedDropdownFilter),
        ("user_groups", MultipleRelatedDropdownFilter),
        ("devices", MultipleRelatedDropdownFilter),
        ("forbidden_devices", MultipleRelatedDropdownFilter),
    )

    fieldsets = (
        ("Основная информация", {"fields": ("name", "description", "created_at")}),
        ("Доступ к оборудованию", {"fields": ("devices", "forbidden_devices")}),
        ("Пользователи и группы", {"fields": ("users", "user_groups")}),
    )

    readonly_fields = ("created_at",)

    @admin.display(description="Описание")
    def description_short(self, obj):
        return (
            (obj.description[:75] + "...")
            if obj.description and len(obj.description) > 75
            else obj.description
        )

    @admin.display(description="Кол-во устройств access")
    def devices_count(self, obj):
        return obj.devices.count()

    @admin.display(description="Кол-во устройств forbidden")
    def forbidden_devices_count(self, obj: AccessGroup):
        return obj.forbidden_devices.count()

    @admin.display(description="Кол-во пользователей")
    def users_count(self, obj):
        return obj.users.count() + obj.user_groups.count()

    class Media:
        css = {
            "all": ("admin/css/widgets.css",),
        }


@admin.register(InterfacesComments)
class InterfacesCommentsAdmin(ModelAdmin):
    """Browse interface comments left by operators."""

    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = True
    list_display = ("device", "interface", "user", "datetime")
    search_fields = ("device__name", "device__ip", "interface", "comment", "user__username")
    list_select_related = ("device", "user")
    autocomplete_fields = ("device", "user")
    readonly_fields = ("datetime",)
    list_filter = (
        ("device", RelatedDropdownFilter),
        ("user", RelatedDropdownFilter),
        ("datetime", RangeDateTimeFilter),
    )
