from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save


class DeviceGroup(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    description = models.TextField(max_length=255, null=True, blank=True, verbose_name='Описание')

    def __str__(self):
        return f'[ {self.name} ]'

    class Meta:
        db_table = 'device_groups'
        ordering = ('name',)
        verbose_name = 'Device group'
        verbose_name_plural = 'Device groups'


class AuthGroup(models.Model):
    """Группа авторизации для удаленного подключения к сетевым устройствам"""
    name = models.CharField(max_length=100, null=False, verbose_name='Название')
    login = models.CharField(max_length=64, null=False, verbose_name='Логин')
    password = models.CharField(max_length=64, null=False, verbose_name='Пароль')
    secret = models.CharField(max_length=64, null=True, blank=True, verbose_name='Пароль от привилегированного режима')
    description = models.TextField(max_length=255, null=True, blank=True, verbose_name='Описание')

    def __str__(self):
        return f'< {self.name} >'

    class Meta:
        db_table = 'device_auth_groups'
        ordering = ('id',)
        verbose_name = 'Auth group'
        verbose_name_plural = 'Auth groups'


class Devices(models.Model):
    """Модель для сетевых устройств"""

    PROTOCOLS = (
        ('snmp', 'snmp'),
        ('telnet', 'telnet'),
        ('ssh', 'ssh')
    )

    group = models.ForeignKey(
        DeviceGroup, on_delete=models.SET_NULL, null=True, verbose_name='Группа'
    )
    ip = models.GenericIPAddressField(
        protocol='ipv4',
        null=False, unique=True, verbose_name='IP адрес', help_text='ipv4'
    )
    name = models.CharField(
        max_length=100, null=False, unique=True,
        verbose_name='Имя оборудования', help_text='Уникальное поле'
    )
    model = models.CharField(
        max_length=100, null=True, blank=True,
        verbose_name='Модель', help_text='Если не указано, то обновится автоматически при подключении к устройству'
    )
    vendor = models.CharField(
        max_length=100, null=True, blank=True,
        verbose_name='Производитель',
        help_text='Если не указано, то обновится автоматически при подключении к устройству'
    )
    auth_group = models.ForeignKey(
        AuthGroup, on_delete=models.SET_NULL, null=True,
        verbose_name='Группа авторизации', help_text='Указываем группу, для удаленного подключения к оборудованию. '
                                                     'Используется для протоколов telnet и ssh. Если на оборудовании '
                                                     'логин/пароль из указанной группы не подошли, то будут '
                                                     'автоматически подбираться пары логин/пароль по очереди, указанной'
                                                     ' в этом списке (кроме неверного)'
    )
    snmp_community = models.CharField(
        max_length=64, null=True, blank=True,
        verbose_name='SNMP community', help_text='Версия - v2c. Используется для сбора интерфейсов, если указан '
                                                 'протокол - SNMP'
    )
    port_scan_protocol = models.CharField(
        choices=PROTOCOLS, max_length=6, default='telnet', null=False,
        verbose_name='Протокол для поиска интерфейсов', help_text='Выберите протокол, с помощью которого будет '
                                                                  'осуществляться сканирование интерфейсов'
    )
    cmd_protocol = models.CharField(
        choices=PROTOCOLS[1:], max_length=6, default='telnet', null=False,
        verbose_name='Протокол для выполнения команд', help_text='Выберите протокол, с помощью которого будет '
                                                                 'осуществляться подключение для вызова команд '
                                                                 '(например: поиск MAC адресов или сброс порта)'
    )

    def __str__(self):
        return f'{self.name} ({self.ip})'

    def get_absolute_url(self):
        return f'/device/{self.name}'

    class Meta:
        db_table = 'devices'
        indexes = [
            models.Index(fields=['ip'], name='device_ip_index')
        ]
        ordering = ('name',)
        verbose_name = 'Device'
        verbose_name_plural = 'Devices'


class Bras(models.Model):
    """
    Модель для маршрутизаторов широкополосного удалённого доступа (BRAS - Broadband Remote Access Server)
    """
    name = models.CharField(max_length=10, null=False, verbose_name='Название')
    ip = models.GenericIPAddressField(
        protocol='ipv4',
        null=False,
        unique=True,
        verbose_name='IP адрес'
    )
    login = models.CharField(max_length=64, null=False, verbose_name='Логин')
    password = models.CharField(max_length=64, null=False, verbose_name='Пароль')
    secret = models.CharField(max_length=64, null=True, blank=True, verbose_name='Пароль от привилегированного режима')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'brases'
        ordering = ('name',)
        verbose_name = 'BRAS'
        verbose_name_plural = 'BRASes'


class Profile(models.Model):
    READ = 'read'
    REBOOT = 'reboot'
    UP_DOWN = 'up_down'
    BRAS = 'bras'

    permissions_level = [READ, REBOOT, UP_DOWN, BRAS]

    PERMS = (
        (READ, 'Чтение'),
        (REBOOT, 'Перезагрузка порта'),
        (UP_DOWN, 'Изменение состояния порта'),
        (BRAS, 'Сброс сессий клиента')
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, verbose_name='Пользователь')
    permissions = models.CharField(choices=PERMS, default=READ, max_length=15, verbose_name='Уровень доступа')
    devices_groups = models.ManyToManyField(DeviceGroup, verbose_name='Доступные группы оборудования')

    def __str__(self):
        return f'Profile: {self.user.username}'

    class Meta:
        db_table = 'user_profiles'
        ordering = ('user',)
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


class UsersActions(models.Model):

    time = models.DateTimeField(auto_now_add=True, verbose_name='Дата/время')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    device = models.ForeignKey(Devices, on_delete=models.CASCADE, null=True, verbose_name='Оборудование')
    action = models.TextField(max_length=1024, verbose_name='Действия')

    class Meta:
        db_table = 'users_actions'
        ordering = ('-time',)
        indexes = [
            models.Index(
                fields=['time'],
                name='logs_time_index'
            )
        ]
        verbose_name = 'User Action'
        verbose_name_plural = 'Users Actions'

    def __str__(self):
        return f'{self.time.strftime("%d.%m.%Y %H:%M:%S")} |' \
               f' {self.user.username:<10} | {self.device or ""} |' \
               f' {self.action}'


class SingletonModel(models.Model):
    """Singleton Django Model
    Ensures there's always only one entry in the database, and can fix the
    table (by deleting extra entries) even if added via another mechanism.
    Also has a static load() method which always returns the object - from
    the database if possible, or a new empty (default) instance if the
    database is still empty. If your instance has sane defaults (recommended),
    you can use it immediately without worrying if it was saved to the
    database or not.
    Useful for things like system-wide user-editable settings.
    """

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """
        Save object to the database. Removes all other entries if there
        are any.
        """
        self.__class__.objects.exclude(id=self.id).delete()
        super(SingletonModel, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        """
        Load object from the database. Failing that, create a new empty
        (default) instance of the object and return it (without saving it
        to the database).
        """
        try:
            return cls.objects.get()
        except cls.DoesNotExist:
            return cls()


class LogsElasticStackSettings(SingletonModel):
    """
    Настройки для отображения логов в Elastic Stack (Singleton)
    """
    kibana_url = models.CharField(
        null=True, blank=True,
        max_length=100, verbose_name="Kibana discover URL", help_text="Например: http://kibana:5601/app/discover#/"
    )
    time_range = models.CharField(
        null=True, blank=True,
        max_length=4, verbose_name="Глубина временного диапазона", help_text="Например: 1d, 24h или 30m"
    )
    output_columns = models.CharField(
        null=True, blank=True,
        max_length=255, verbose_name='Колонки',
        help_text="Поля через запятую, которые должны отображаться как колонки.<br> Например: message,host.ip"
    )

    QUERY_LANGS = (
        ('KQL', 'KQL'),
        ('Lucene', 'Lucene')
    )
    query_lang = models.CharField(
        null=True, blank=True,
        choices=QUERY_LANGS, max_length=10, verbose_name="Язык запросов", default='KQL',
        help_text='<a target="_blank" href="https://www.elastic.co/guide/en/kibana/8.4/kuery-query.html">'
                  'Documentation</a>'
    )
    query_str = models.CharField(
        null=True, blank=True,
        max_length=255, verbose_name="Строка для поиска",
        help_text="Необходимо указать, как будет произведен поиск логов для отдельного устройства.<br>"
                  "Доступны следующие переменные:<br>"
                  "{device.ip}<br>"
                  "{device.name}<br>"
                  "{device.vendor}<br>"
                  "{device.model}<br>"
                  "Пример строки: host.ip : {device.ip}"
    )
    time_field = models.CharField(
        null=True, blank=True,
        max_length=100, verbose_name="timestamp поле", help_text="Сортировка будет происходить по нему.<br>"
                                                                 "Например: @timestamp"
    )

    def __str__(self):
        return "Elastic Stack settings"

    def is_set(self):
        """ Проверяет, настройки имеются или нет """
        return self.kibana_url and self.time_range and self.time_field and self.query_str

    class Meta:
        verbose_name_plural = 'Elastic Stack settings'
        verbose_name = 'Elastic Stack settings'


@receiver(post_save, sender=User)
def auto_create_profile(sender, instance: User, created: bool, **kwargs):
    if created:
        Profile.objects.create(
            user=instance
        )
