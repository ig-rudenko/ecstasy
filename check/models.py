"""

# Модели для оборудования

"""

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils.text import slugify
from ping3 import ping

from devicemanager.dc import SimpleAuthObject
from devicemanager.remote import remote_connector
from devicemanager.remote.connector import RemoteDevice


class DeviceGroup(models.Model):
    """Группа для оборудования"""

    name = models.CharField(max_length=100, verbose_name="Название")
    description = models.TextField(max_length=255, null=True, blank=True, verbose_name="Описание")

    def __str__(self):
        return f"[ {self.name} ]"

    class Meta:
        db_table = "device_groups"
        ordering = ("name",)
        verbose_name = "Device group"
        verbose_name_plural = "Device groups"


class AuthGroup(models.Model):
    """Группа авторизации для удаленного подключения к сетевым устройствам"""

    name = models.CharField(max_length=100, null=False, verbose_name="Название")
    login = models.CharField(max_length=64, null=False, verbose_name="Логин")
    password = models.CharField(max_length=64, null=False, verbose_name="Пароль")
    secret = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name="Пароль от привилегированного режима",
    )
    description = models.TextField(max_length=255, null=True, blank=True, verbose_name="Описание")

    def __str__(self):
        return f"< {self.name} >"

    class Meta:
        db_table = "device_auth_groups"
        ordering = ("id",)
        verbose_name = "Auth group"
        verbose_name_plural = "Auth groups"


class Devices(models.Model):
    """Модель для сетевых устройств"""

    PROTOCOLS = (("snmp", "snmp"), ("telnet", "telnet"), ("ssh", "ssh"))

    group = models.ForeignKey(DeviceGroup, on_delete=models.SET_NULL, null=True, verbose_name="Группа")
    ip = models.GenericIPAddressField(
        protocol="ipv4",
        null=False,
        unique=True,
        verbose_name="IP адрес",
        help_text="ipv4",
    )
    name = models.CharField(
        max_length=100,
        null=False,
        unique=True,
        verbose_name="Имя оборудования",
        help_text="Уникальное поле",
    )
    model = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Модель",
        help_text="Если не указано, то обновится автоматически при подключении к устройству",
    )
    vendor = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Производитель",
        help_text="Если не указано, то обновится автоматически при подключении к устройству",
    )
    serial_number = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Серийный номер",
        help_text="Если не указано, то обновится автоматически при подключении к устройству",
    )
    auth_group = models.ForeignKey(
        AuthGroup,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Группа авторизации",
        help_text="Указываем группу, для удаленного подключения к оборудованию. "
        "Используется для протоколов telnet и ssh. Если на оборудовании "
        "логин/пароль из указанной группы не подошли, то будут "
        "автоматически подбираться пары логин/пароль по очереди, указанной"
        " в этом списке (кроме неверного)",
    )
    snmp_community = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name="SNMP community",
        help_text="Версия - v2c. Используется для сбора интерфейсов, если указан " "протокол - SNMP",
    )
    port_scan_protocol = models.CharField(
        choices=PROTOCOLS,
        max_length=6,
        default="telnet",
        null=False,
        verbose_name="Протокол для поиска интерфейсов",
        help_text="Выберите протокол, с помощью которого будет " "осуществляться сканирование интерфейсов",
    )
    cmd_protocol = models.CharField(
        choices=PROTOCOLS[1:],
        max_length=6,
        default="telnet",
        null=False,
        verbose_name="Протокол для выполнения команд",
        help_text="Выберите протокол, с помощью которого будет "
        "осуществляться подключение для вызова команд "
        "(например: поиск MAC адресов или сброс порта)",
    )
    interface_pattern = models.CharField(
        default="",
        blank=True,
        max_length=255,
        verbose_name="Паттерн имени интерфейса",
        help_text=r"Паттерн, по которому отфильтрованы интерфейсы. "
        r"Например `^gi\S+|^eth\S+`. По умолчанию все интерфейсы.",
    )
    active = models.BooleanField(
        default=True,
        verbose_name="Активно",
    )
    collect_interfaces = models.BooleanField(
        default=True,
        verbose_name="Сбор интерфейсов",
        help_text="Если включено, то будут собраны интерфейсы "
        'во время периодической задачи "interfaces_scan"',
    )
    collect_mac_addresses = models.BooleanField(
        default=True,
        verbose_name="Сбор MAC адресов",
        help_text="Если включено, то будут собраны MAC адреса "
        'во время периодической задачи "mac_table_gather_task"',
    )
    collect_configurations = models.BooleanField(
        default=True,
        verbose_name="Сбор конфигураций",
        help_text="Если включено, то будут собраны конфигурации "
        'во время периодической задачи "configuration_gather_task"',
    )
    connection_pool_size = models.PositiveSmallIntegerField(
        default=2,
        verbose_name="Размер пула подключений",
        help_text="Количество подключений к оборудованию, которые могут быть одновременно открыты",
    )

    def __str__(self):
        return f"{self.name} ({self.ip})"

    def get_absolute_url(self):
        """Возвращает ссылку, которая ведет к просмотру оборудования"""

        return f"/device/{self.name}"

    @property
    def available(self) -> bool:
        p = ping(self.ip, timeout=2)
        return isinstance(p, float)

    def connect(self, make_session_global=True) -> RemoteDevice:
        """Удаленное подключение к оборудованию"""

        return remote_connector.create(
            ip=self.ip,
            cmd_protocol=self.cmd_protocol,
            port_scan_protocol=self.port_scan_protocol,
            snmp_community=str(self.snmp_community),
            auth_obj=self.auth_group,
            make_session_global=make_session_global,
            pool_size=self.connection_pool_size,
        )

    class Meta:
        db_table = "devices"
        indexes = [models.Index(fields=["ip"], name="device_ip_index")]
        ordering = ("name",)
        verbose_name = "Device"
        verbose_name_plural = "Devices"


def get_device_media_path(instance, file_name: str) -> str:
    slug = slugify(instance.device.name, allow_unicode=True)
    return f"{slug}/{file_name}"


class DeviceMedia(models.Model):
    device = models.ForeignKey(Devices, on_delete=models.CASCADE, related_name="medias")
    file = models.FileField(upload_to=get_device_media_path)
    description = models.CharField(max_length=1024, null=True, blank=True)
    mod_time = models.DateTimeField(auto_now=True)

    @property
    def file_type(self) -> str:
        return self.file.path.rsplit(".")[-1]

    @property
    def is_image(self) -> bool:
        return self.file_type.lower() in ["png", "jpeg", "jpg", "bmp", "gif", "svg"]

    @property
    def file_name(self):
        return self.file.name.rsplit("/")[-1]

    class Meta:
        db_table = "device_media"
        verbose_name = "Медиафайл"
        verbose_name_plural = "Медиафайлы"


@receiver(pre_delete, sender=DeviceMedia)
def delete_files(sender, instance: DeviceMedia, **kwargs):
    instance.file.delete()


class Bras(models.Model):
    """
    Модель для маршрутизаторов широкополосного удалённого доступа (BRAS - Broadband Remote Access Server)
    """

    name = models.CharField(max_length=10, null=False, verbose_name="Название")
    ip = models.GenericIPAddressField(protocol="ipv4", null=False, unique=True, verbose_name="IP адрес")
    login = models.CharField(max_length=64, null=False, verbose_name="Логин")
    password = models.CharField(max_length=64, null=False, verbose_name="Пароль")
    secret = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name="Пароль от привилегированного режима",
    )
    connection_pool_size = models.PositiveSmallIntegerField(
        default=2,
        verbose_name="Размер пула подключений",
        help_text="Количество подключений к оборудованию, которые могут быть одновременно открыты",
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "brases"
        ordering = ("name",)
        verbose_name = "BRAS"
        verbose_name_plural = "BRASes"

    def connect(self) -> RemoteDevice:
        return remote_connector.create(
            ip=self.ip,
            cmd_protocol="telnet",
            port_scan_protocol="telnet",
            snmp_community="",
            auth_obj=SimpleAuthObject(self.login, self.password, self.secret or ""),
            make_session_global=True,
            pool_size=self.connection_pool_size,
        )

    @staticmethod
    def format_mac(mac_str: str) -> str:
        return "{}{}{}{}-{}{}{}{}-{}{}{}{}".format(*mac_str)


class Profile(models.Model):
    """Профиль пользователя"""

    READ = "read"
    REBOOT = "reboot"
    UP_DOWN = "up_down"
    BRAS = "bras"

    permissions_level = [READ, REBOOT, UP_DOWN, BRAS]

    PERMS = (
        (READ, "Чтение"),
        (REBOOT, "Перезагрузка порта"),
        (UP_DOWN, "Изменение состояния порта"),
        (BRAS, "Сброс сессий клиента"),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, verbose_name="Пользователь")
    permissions = models.CharField(choices=PERMS, default=READ, max_length=15, verbose_name="Уровень доступа")
    devices_groups = models.ManyToManyField(DeviceGroup, verbose_name="Доступные группы оборудования")
    port_guard_pattern = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Защитный RegExp для описания порта",
        help_text="Регулярное выражение, совпадение которого с описанием"
        " порта будет запрещать определенные действия с ним",
    )
    console_access = models.BooleanField(
        default=False,
        verbose_name="Доступ к консоли",
        help_text="Доступ к консоли сервера удаленных подключений",
    )
    console_url = models.CharField(default="", max_length=500, blank=True, verbose_name="URL консоли")

    @property
    def perm_level(self) -> int:
        return self.permissions_level.index(self.permissions)

    def __str__(self):
        return f"Profile: {self.user.username}"

    class Meta:
        db_table = "user_profiles"
        ordering = ("user",)
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


class UsersActions(models.Model):
    """Логирование действий пользователя"""

    time = models.DateTimeField(auto_now_add=True, verbose_name="Дата/время")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    device = models.ForeignKey(Devices, on_delete=models.CASCADE, null=True, verbose_name="Оборудование")
    action = models.TextField(max_length=1024, verbose_name="Действия")

    class Meta:
        db_table = "users_actions"
        ordering = ("-time",)
        indexes = [models.Index(fields=["time"], name="logs_time_index")]
        verbose_name = "User Action"
        verbose_name_plural = "Users Actions"

    def __str__(self):
        return (
            f'{self.time.strftime("%d.%m.%Y %H:%M:%S")} |'
            f' {self.user.username:<10} | {self.device or ""} |'
            f" {self.action}"
        )


class InterfacesComments(models.Model):
    device = models.ForeignKey(Devices, on_delete=models.CASCADE)
    interface = models.CharField(max_length=100, null=False, blank=False)
    comment = models.TextField(null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    datetime = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"InterfaceComment: {self.device.name} ({self.interface})"

    class Meta:
        db_table = "interfaces_comments"
        verbose_name = "Комментарий к интерфейсу"
        verbose_name_plural = "Комментарии к интерфейсам"


@receiver(post_save, sender=User)
def auto_create_profile(sender, instance: User, created: bool, **kwargs):
    """Автоматически создаем профиль пользователя после его создания"""

    if created:
        Profile.objects.create(user=instance)
