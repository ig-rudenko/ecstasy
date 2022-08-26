from django.db import models
from django.contrib.auth.models import User


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
    name = models.CharField(max_length=100, null=False, verbose_name='Название')
    login = models.CharField(max_length=64, null=False, verbose_name='Логин')
    password = models.CharField(max_length=64, null=False, verbose_name='Пароль')
    secret = models.CharField(max_length=64, null=True, blank=True, verbose_name='Пароль от привилегированного режима')
    description = models.TextField(max_length=255, null=True, blank=True, verbose_name='Описание')

    def __str__(self):
        return f'< {self.name} >'

    class Meta:
        db_table = 'device_auth_groups'
        ordering = ('name',)
        verbose_name = 'Auth group'
        verbose_name_plural = 'Auth groups'


class Devices(models.Model):
    PROTOCOLS = (
        ('snmp', 'snmp'),
        ('telnet', 'telnet'),
        ('ssh', 'ssh')
    )

    group = models.ForeignKey(DeviceGroup, on_delete=models.SET_NULL, null=True, verbose_name='Группа')
    ip = models.CharField(max_length=15, null=False, unique=True, verbose_name='IP адрес')
    name = models.CharField(max_length=100, null=False, unique=True, verbose_name='Имя оборудования')
    model = models.CharField(max_length=100, null=True, blank=True, verbose_name='Модель')
    vendor = models.CharField(max_length=100, null=True, verbose_name='Производитель')
    auth_group = models.ForeignKey(AuthGroup, on_delete=models.SET_NULL, null=True, verbose_name='Группа авторизации')
    snmp_community = models.CharField(max_length=64, null=True, blank=True, verbose_name='(SNMP v2c) community')
    protocol = models.CharField(choices=PROTOCOLS, max_length=6, default='telnet', verbose_name='Протокол для поиска '
                                                                                                'интерфейсов')

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
    name = models.CharField(max_length=10, null=False, verbose_name='Название')
    ip = models.CharField(max_length=15, null=False, unique=True, verbose_name='IP адрес')
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

    permissions_level = ['read', 'reboot', 'up_down', 'bras']

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
