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
from django.db.models import QuerySet
from django.http import HttpResponse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from import_export.admin import ExportMixin

from devicemanager.device import Interfaces
from gathering.services.configurations import LocalConfigStorage
from .export import DevicesInterfacesWorkloadExcelExport
from .export_resources import DevicesResource
from .models import (
    DeviceGroup,
    Devices,
    AuthGroup,
    Bras,
    Profile,
    UsersActions,
    DeviceMedia,
    DeviceCommand,
)


class ProfileInline(admin.TabularInline):
    model = Profile.devices_groups.through


@admin.register(DeviceGroup)
class DeviceGroupAdmin(admin.ModelAdmin):
    """Управление группами оборудования"""

    list_display = ["name", "description", "dev_count"]
    inlines = [ProfileInline]

    @admin.display(description="Кол-во")
    def dev_count(self, obj: DeviceGroup) -> int:
        return obj.devices_set.count()


@admin.register(Devices)
class DevicesAdmin(ExportMixin, admin.ModelAdmin):
    """Управление оборудованием"""

    resource_class = DevicesResource

    list_display = [
        "ip",
        "name",
        "vendor",
        "model",
        "show_group",
        "show_auth_group",
        "show_auth_type",
        "show_device",
    ]
    list_filter = [
        "vendor",
        "group",
        "auth_group",
        "model",
        "port_scan_protocol",
        "cmd_protocol",
        "connection_pool_size",
    ]
    radio_fields = {
        "port_scan_protocol": admin.HORIZONTAL,
        "cmd_protocol": admin.HORIZONTAL,
    }
    readonly_fields = ["show_interfaces"]
    search_fields = ["ip", "name"]
    list_select_related = ["auth_group", "group"]
    list_per_page = 50

    fieldsets = (
        (
            "Характеристика",
            {"fields": ("ip", "name", "active"), "classes": ("wide",)},
        ),
        (
            "Тип",
            {"fields": ("vendor", "model", "serial_number")},
        ),
        (
            "Принадлежность",
            {"fields": ("group", "auth_group")},
        ),
        (
            "Удаленное подключение",
            {
                "fields": (
                    "snmp_community",
                    "port_scan_protocol",
                    "cmd_protocol",
                    "collect_interfaces",
                    "collect_mac_addresses",
                    "collect_vlan_info",
                    "collect_configurations",
                    "connection_pool_size",
                )
            },
        ),
        (
            "Интерфейсы",
            {"fields": ("interface_pattern", "show_interfaces")},
        ),
    )
    actions = [
        "excel_interfaces_export",
        "load_last_config_files",
        "set_telnet",
        "set_snmp",
        "set_ssh",
        "set_pool_size_1",
        "set_pool_size_2",
        "set_pool_size_3",
        "set_pool_size_4",
    ]

    @admin.display(description="Группа")
    def show_group(self, obj: Devices):
        return obj.group.name if obj.group else "Не указано"

    @admin.display(description="Авторизация")
    def show_auth_group(self, obj: Devices):
        return obj.auth_group.name if obj.auth_group else "Не указано"

    @admin.display(description="")
    def show_auth_type(self, obj: Devices):
        text = ""
        if obj.port_scan_protocol == "telnet":
            text += """<span class="ml-1" title="telnet"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#ff8591" class="bi bi-shield-lock-fill" viewBox="0 0 16 16">
                      <path fill-rule="evenodd" d="M8 0c-.69 0-1.843.265-2.928.56-1.11.3-2.229.655-2.887.87a1.54 1.54 0 0 0-1.044 1.262c-.596 4.477.787 7.795 2.465 9.99a11.8 11.8 0 0 0 2.517 2.453c.386.273.744.482 1.048.625.28.132.581.24.829.24s.548-.108.829-.24a7 7 0 0 0 1.048-.625 11.8 11.8 0 0 0 2.517-2.453c1.678-2.195 3.061-5.513 2.465-9.99a1.54 1.54 0 0 0-1.044-1.263 63 63 0 0 0-2.887-.87C9.843.266 8.69 0 8 0m0 5a1.5 1.5 0 0 1 .5 2.915l.385 1.99a.5.5 0 0 1-.491.595h-.788a.5.5 0 0 1-.49-.595l.384-1.99A1.5 1.5 0 0 1 8 5"/>
                    </svg></span>"""
        elif obj.port_scan_protocol == "ssh":
            text += """<span class="ml-1" title="ssh"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="orange" class="bi bi-shield-lock-fill" viewBox="0 0 16 16">
                      <path fill-rule="evenodd" d="M8 0c-.69 0-1.843.265-2.928.56-1.11.3-2.229.655-2.887.87a1.54 1.54 0 0 0-1.044 1.262c-.596 4.477.787 7.795 2.465 9.99a11.8 11.8 0 0 0 2.517 2.453c.386.273.744.482 1.048.625.28.132.581.24.829.24s.548-.108.829-.24a7 7 0 0 0 1.048-.625 11.8 11.8 0 0 0 2.517-2.453c1.678-2.195 3.061-5.513 2.465-9.99a1.54 1.54 0 0 0-1.044-1.263 63 63 0 0 0-2.887-.87C9.843.266 8.69 0 8 0m0 5a1.5 1.5 0 0 1 .5 2.915l.385 1.99a.5.5 0 0 1-.491.595h-.788a.5.5 0 0 1-.49-.595l.384-1.99A1.5 1.5 0 0 1 8 5"/>
                    </svg></span>"""
        elif obj.port_scan_protocol == "snmp":
            text += """<span class="ml-1" style="color: green;font-family: fantasy;">SNMP</span>"""

        if obj.cmd_protocol != obj.port_scan_protocol:
            if obj.cmd_protocol == "telnet":
                text += """<span title="telnet"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#ff8591" class="bi bi-shield-lock-fill" viewBox="0 0 16 16">
                          <path fill-rule="evenodd" d="M8 0c-.69 0-1.843.265-2.928.56-1.11.3-2.229.655-2.887.87a1.54 1.54 0 0 0-1.044 1.262c-.596 4.477.787 7.795 2.465 9.99a11.8 11.8 0 0 0 2.517 2.453c.386.273.744.482 1.048.625.28.132.581.24.829.24s.548-.108.829-.24a7 7 0 0 0 1.048-.625 11.8 11.8 0 0 0 2.517-2.453c1.678-2.195 3.061-5.513 2.465-9.99a1.54 1.54 0 0 0-1.044-1.263 63 63 0 0 0-2.887-.87C9.843.266 8.69 0 8 0m0 5a1.5 1.5 0 0 1 .5 2.915l.385 1.99a.5.5 0 0 1-.491.595h-.788a.5.5 0 0 1-.49-.595l.384-1.99A1.5 1.5 0 0 1 8 5"/>
                        </svg></span>"""
            elif obj.cmd_protocol == "ssh":
                text += """<span title="ssh"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="orange" class="bi bi-shield-lock-fill" viewBox="0 0 16 16">
                          <path fill-rule="evenodd" d="M8 0c-.69 0-1.843.265-2.928.56-1.11.3-2.229.655-2.887.87a1.54 1.54 0 0 0-1.044 1.262c-.596 4.477.787 7.795 2.465 9.99a11.8 11.8 0 0 0 2.517 2.453c.386.273.744.482 1.048.625.28.132.581.24.829.24s.548-.108.829-.24a7 7 0 0 0 1.048-.625 11.8 11.8 0 0 0 2.517-2.453c1.678-2.195 3.061-5.513 2.465-9.99a1.54 1.54 0 0 0-1.044-1.263 63 63 0 0 0-2.887-.87C9.843.266 8.69 0 8 0m0 5a1.5 1.5 0 0 1 .5 2.915l.385 1.99a.5.5 0 0 1-.491.595h-.788a.5.5 0 0 1-.49-.595l.384-1.99A1.5 1.5 0 0 1 8 5"/>
                        </svg></span>"""

        return mark_safe(text)

    @admin.display(description="Интерфейсы")
    def show_interfaces(self, obj: Devices):
        """Выводит табличку интерфейсов оборудования из истории"""
        interfaces = (
            str(Interfaces(orjson.loads(obj.devicesinfo.interfaces or "[]")))
            .replace("\n", "<br>")
            .replace(" ", "&nbsp;")
        )
        return format_html(
            f"""
            <div style"overflow-x: scroll;">
                <div style="font-family: monospace; white-space: nowrap;">
                    {interfaces}
                </div>
            </div>"""
        )

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
        """Меняем протокол поиска интерфейсов на TELNET"""

        queryset.update(port_scan_protocol="telnet")

    @admin.action(description="snmp Протокол для поиска интерфейсов")
    def set_snmp(self, request, queryset):
        """Меняем протокол поиска интерфейсов на SNMP"""

        queryset.update(port_scan_protocol="snmp")

    @admin.action(description="ssh Протокол для поиска интерфейсов")
    def set_ssh(self, request, queryset):
        """Меняем протокол поиска интерфейсов на SSH"""

        queryset.update(port_scan_protocol="ssh")

    @admin.action(description="Установка пула подключений в 1")
    def set_pool_size_1(self, request, queryset):
        queryset.update(connection_pool_size=1)

    @admin.action(description="Установка пула подключений в 2")
    def set_pool_size_2(self, request, queryset):
        queryset.update(connection_pool_size=3)

    @admin.action(description="Установка пула подключений в 3")
    def set_pool_size_3(self, request, queryset):
        queryset.update(connection_pool_size=3)

    @admin.action(description="Установка пула подключений в 4")
    def set_pool_size_4(self, request, queryset):
        queryset.update(connection_pool_size=4)

    @admin.action(description="Экспорт ёмкости интерфейсов в xls")
    def excel_interfaces_export(self, request, queryset):
        """Экспортируем ёмкость интерфейсов в excel файл"""
        export = DevicesInterfacesWorkloadExcelExport(queryset)
        export.make_excel()
        return export.create_response()

    @admin.action(description="Скачать последние конфигурации ZIP")
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
class AuthGroupAdmin(admin.ModelAdmin):
    """Взаимодействие с профилями авторизации к оборудованию"""

    list_display = ["name", "login", "description", "dev_count"]
    search_fields = ["name", "login"]

    @admin.display(description="Кол-во")
    def dev_count(self, obj: AuthGroup) -> int:
        return obj.devices_set.count()


@admin.register(Bras)
class BrasAdmin(admin.ModelAdmin):
    """Настройка для маршрутизаторов широкополосного удалённого доступа BRAS"""

    list_display = ["name", "ip"]
    search_fields = ["name", "ip"]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Управление уровнем привилегий пользователей"""

    list_display = ["user", "permissions", "dev_groups", "console_access"]
    list_select_related = ["user"]
    filter_horizontal = ["devices_groups"]

    @admin.display(description="Пользователь")
    def user(self, obj: Profile):
        """Отображаем username пользователя"""
        return obj.user.username

    @admin.display(description="Группы")
    def dev_groups(self, obj: Profile):
        """Отображение доступных групп для пользователя"""
        user_groups: QuerySet[DeviceGroup] = obj.devices_groups.all()
        groups_string = "".join([f"<li>{group.name}</li>" for group in user_groups])
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

        user_groups: QuerySet[DeviceGroup] = profile.devices_groups.all()
        groups_string = "".join([f"<li>{group}</li>" for group in user_groups])
        return mark_safe(groups_string)


@admin.register(UsersActions)
class UsersActionsAdmin(admin.ModelAdmin):
    """Просмотр логов действий пользователя"""

    list_display = ["time", "user", "device", "action"]
    list_filter = ["user"]
    search_fields = ["action"]
    date_hierarchy = "time"
    readonly_fields = ["time", "user", "device", "action"]
    list_per_page = 50


@admin.register(DeviceMedia)
class DeviceMediaAdmin(admin.ModelAdmin):
    list_display = ["file_type", "file_name", "current_file"]
    search_fields = ["device__name"]
    list_select_related = ["device"]

    fieldsets = (
        (
            None,
            {"fields": ("description", "device", ("current_file", "file"))},
        ),
    )

    readonly_fields = ["current_file"]

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
        return obj.file.name

    @staticmethod
    def current_file(obj: DeviceMedia) -> str:
        if obj.is_image:
            return mark_safe(f'<img src="{obj.file.url}" style="max-height: 300px;" >')

        if obj.file_type == "pdf":
            return mark_safe(
                f"""<a href="{obj.file.url}"><svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" fill="currentColor" class="bi bi-file-earmark-pdf" viewBox="0 0 16 16">
                      <path d="M14 14V4.5L9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2zM9.5 3A1.5 1.5 0 0 0 11 4.5h2V14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h5.5v2z"/>
                      <path d="M4.603 14.087a.81.81 0 0 1-.438-.42c-.195-.388-.13-.776.08-1.102.198-.307.526-.568.897-.787a7.68 7.68 0 0 1 1.482-.645 19.697 19.697 0 0 0 1.062-2.227 7.269 7.269 0 0 1-.43-1.295c-.086-.4-.119-.796-.046-1.136.075-.354.274-.672.65-.823.192-.077.4-.12.602-.077a.7.7 0 0 1 .477.365c.088.164.12.356.127.538.007.188-.012.396-.047.614-.084.51-.27 1.134-.52 1.794a10.954 10.954 0 0 0 .98 1.686 5.753 5.753 0 0 1 1.334.05c.364.066.734.195.96.465.12.144.193.32.2.518.007.192-.047.382-.138.563a1.04 1.04 0 0 1-.354.416.856.856 0 0 1-.51.138c-.331-.014-.654-.196-.933-.417a5.712 5.712 0 0 1-.911-.95 11.651 11.651 0 0 0-1.997.406 11.307 11.307 0 0 1-1.02 1.51c-.292.35-.609.656-.927.787a.793.793 0 0 1-.58.029zm1.379-1.901c-.166.076-.32.156-.459.238-.328.194-.541.383-.647.547-.094.145-.096.25-.04.361.01.022.02.036.026.044a.266.266 0 0 0 .035-.012c.137-.056.355-.235.635-.572a8.18 8.18 0 0 0 .45-.606zm1.64-1.33a12.71 12.71 0 0 1 1.01-.193 11.744 11.744 0 0 1-.51-.858 20.801 20.801 0 0 1-.5 1.05zm2.446.45c.15.163.296.3.435.41.24.19.407.253.498.256a.107.107 0 0 0 .07-.015.307.307 0 0 0 .094-.125.436.436 0 0 0 .059-.2.095.095 0 0 0-.026-.063c-.052-.062-.2-.152-.518-.209a3.876 3.876 0 0 0-.612-.053zM8.078 7.8a6.7 6.7 0 0 0 .2-.828c.031-.188.043-.343.038-.465a.613.613 0 0 0-.032-.198.517.517 0 0 0-.145.04c-.087.035-.158.106-.196.283-.04.192-.03.469.046.822.024.111.054.227.09.346z"/>
                    </svg></a>"""
            )

        return ""


class DeviceCommandModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uniq_vendors = list(sorted(set(Devices.objects.all().values_list("vendor", flat=True)), key=str))
        self.fields["device_vendor"] = forms.ChoiceField(choices=[(v, v) for v in uniq_vendors], required=True)

    class Meta:
        model = DeviceCommand
        fields = ["name", "description", "command", "device_vendor", "perm_groups"]


@admin.register(DeviceCommand)
class DeviceCommandAdmin(admin.ModelAdmin):
    list_display = ["name", "device_vendor", "command", "description"]
    search_fields = ["name", "command"]
    form = DeviceCommandModelForm
    list_filter = ["device_vendor"]
