"""

# Модели для оборудования

"""

from ping3 import ping

from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from devicemanager.dc import DeviceFactory
from devicemanager.dc import SimpleAuthObject


class DeviceGroup(models.Model):
    """Группа для оборудования"""

    name = models.CharField(max_length=100, verbose_name="Название")
    description = models.TextField(
        max_length=255, null=True, blank=True, verbose_name="Описание"
    )

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
    description = models.TextField(
        max_length=255, null=True, blank=True, verbose_name="Описание"
    )

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

    group = models.ForeignKey(
        DeviceGroup, on_delete=models.SET_NULL, null=True, verbose_name="Группа"
    )
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
        help_text="Версия - v2c. Используется для сбора интерфейсов, если указан "
        "протокол - SNMP",
    )
    port_scan_protocol = models.CharField(
        choices=PROTOCOLS,
        max_length=6,
        default="telnet",
        null=False,
        verbose_name="Протокол для поиска интерфейсов",
        help_text="Выберите протокол, с помощью которого будет "
        "осуществляться сканирование интерфейсов",
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

    def __str__(self):
        return f"{self.name} ({self.ip})"

    def get_absolute_url(self):
        """Возвращает ссылку, которая ведет к просмотру оборудования"""

        return f"/device/{self.name}"

    @property
    def available(self) -> bool:
        return ping(self.ip, timeout=2) > 0

    def connect(self, **kwargs) -> DeviceFactory:
        """Удаленное подключение к оборудованию"""

        return DeviceFactory(
            self.ip, protocol=self.cmd_protocol, auth_obj=self.auth_group, **kwargs
        )

    class Meta:
        db_table = "devices"
        indexes = [models.Index(fields=["ip"], name="device_ip_index")]
        ordering = ("name",)
        verbose_name = "Device"
        verbose_name_plural = "Devices"


class Bras(models.Model):
    """
    Модель для маршрутизаторов широкополосного удалённого доступа (BRAS - Broadband Remote Access Server)
    """

    name = models.CharField(max_length=10, null=False, verbose_name="Название")
    ip = models.GenericIPAddressField(
        protocol="ipv4", null=False, unique=True, verbose_name="IP адрес"
    )
    login = models.CharField(max_length=64, null=False, verbose_name="Логин")
    password = models.CharField(max_length=64, null=False, verbose_name="Пароль")
    secret = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name="Пароль от привилегированного режима",
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "brases"
        ordering = ("name",)
        verbose_name = "BRAS"
        verbose_name_plural = "BRASes"

    def connect(self):
        return DeviceFactory(
            ip=self.ip,
            protocol="telnet",
            auth_obj=SimpleAuthObject(self.login, self.password, self.secret),
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
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True, verbose_name="Пользователь"
    )
    permissions = models.CharField(
        choices=PERMS, default=READ, max_length=15, verbose_name="Уровень доступа"
    )
    devices_groups = models.ManyToManyField(
        DeviceGroup, verbose_name="Доступные группы оборудования"
    )

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
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    device = models.ForeignKey(
        Devices, on_delete=models.CASCADE, null=True, verbose_name="Оборудование"
    )
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
