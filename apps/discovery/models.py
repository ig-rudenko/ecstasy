from django.conf import settings
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from apps.check.models import AuthGroup, DeviceGroup, Devices


class DiscoveryProfile(models.Model):
    """Профиль настроек для запуска auto discovery."""

    AUTO_PROTOCOL = "auto"
    PORT_SCAN_PROTOCOLS = (
        (AUTO_PROTOCOL, "Авто (SSH → Telnet)"),
        *Devices.PROTOCOLS,
    )
    CMD_PROTOCOLS = (
        (AUTO_PROTOCOL, "Авто (SSH → Telnet)"),
        *Devices.PROTOCOLS[1:],
    )

    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    networks = models.JSONField(default=list, verbose_name="IPv4 подсети")
    exclude_ips = models.JSONField(default=list, blank=True, verbose_name="Исключенные IP/CIDR")
    device_group = models.ForeignKey(
        DeviceGroup,
        on_delete=models.PROTECT,
        related_name="discovery_profiles",
        verbose_name="Группа оборудования",
    )
    auth_groups = models.ManyToManyField(
        AuthGroup,
        related_name="discovery_profiles",
        blank=True,
        verbose_name="Группы авторизации",
    )
    snmp_communities = models.JSONField(default=list, blank=True, verbose_name="SNMP communities")
    try_protocols = models.JSONField(default=list, blank=True, verbose_name="CLI протоколы")
    port_scan_protocol = models.CharField(
        choices=PORT_SCAN_PROTOCOLS,
        max_length=6,
        default="snmp",
        verbose_name="Протокол сбора интерфейсов",
    )
    cmd_protocol = models.CharField(
        choices=CMD_PROTOCOLS,
        max_length=6,
        default="ssh",
        verbose_name="Протокол выполнения команд",
    )
    max_workers = models.PositiveSmallIntegerField(default=32, verbose_name="Параллельность")
    timeout_seconds = models.PositiveSmallIntegerField(default=2, verbose_name="Таймаут")
    auto_create = models.BooleanField(default=False, verbose_name="Автосоздание")
    auto_create_min_confidence = models.PositiveSmallIntegerField(
        default=70,
        verbose_name="Минимальный confidence для автосоздания",
    )
    activate_created_devices = models.BooleanField(
        default=False,
        verbose_name="Активировать созданное оборудование",
    )
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        db_table = "discovery_profiles"
        ordering = ("name",)
        verbose_name = "Discovery profile"
        verbose_name_plural = "Discovery profiles"

    def __str__(self) -> str:
        """Вернуть имя профиля discovery."""

        return self.name


class DiscoveryRun(models.Model):
    """Один запуск auto discovery."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROGRESS = "PROGRESS", "Progress"
        SUCCESS = "SUCCESS", "Success"
        FAILURE = "FAILURE", "Failure"
        REVOKED = "REVOKED", "Revoked"

    profile = models.ForeignKey(
        DiscoveryProfile,
        on_delete=models.CASCADE,
        related_name="runs",
        verbose_name="Профиль discovery",
    )
    task_id = models.CharField(max_length=255, blank=True, db_index=True, verbose_name="Celery task ID")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,  # noqa
        default=Status.PENDING,
        db_index=True,
        verbose_name="Статус",
    )
    total = models.PositiveIntegerField(default=0, verbose_name="Всего адресов")
    processed = models.PositiveIntegerField(default=0, verbose_name="Обработано")
    found = models.PositiveIntegerField(default=0, verbose_name="Найдено")
    created = models.PositiveIntegerField(default=0, verbose_name="Создано устройств")
    skipped = models.PositiveIntegerField(default=0, verbose_name="Пропущено")
    errors = models.PositiveIntegerField(default=0, verbose_name="Ошибок")
    dry_run = models.BooleanField(default=False, verbose_name="Пробный запуск")
    summary = models.JSONField(default=dict, blank=True, verbose_name="Сводка")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="discovery_runs",
        verbose_name="Запустил",
    )
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата начала")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата завершения")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        db_table = "discovery_runs"
        ordering = ("-created_at",)
        verbose_name = "Discovery run"
        verbose_name_plural = "Discovery runs"

    def __str__(self) -> str:
        """Вернуть человекочитаемое представление запуска discovery."""

        return f"{self.profile.name} | {self.status} | {self.created_at:%Y-%m-%d %H:%M:%S}"


class DiscoveryCandidate(models.Model):
    """Кандидат на добавление в модель Devices."""

    class Source(models.TextChoices):
        PING = "PING", "Ping"
        TCP = "TCP", "TCP"
        SNMP = "SNMP", "SNMP"
        CLI = "CLI", "CLI"
        ZABBIX_IMPORT = "ZABBIX_IMPORT", "Zabbix import"

    class Status(models.TextChoices):
        NEW = "NEW", "New"
        READY = "READY", "Ready"
        DUPLICATE = "DUPLICATE", "Duplicate"
        CREATED = "CREATED", "Created"
        IGNORED = "IGNORED", "Ignored"
        FAILED = "FAILED", "Failed"

    ip = models.GenericIPAddressField(protocol="ipv4", unique=True, verbose_name="IP адрес")
    name = models.CharField(max_length=100, blank=True, verbose_name="Предложенное имя")
    vendor = models.CharField(max_length=100, blank=True, verbose_name="Производитель")
    model = models.CharField(max_length=100, blank=True, verbose_name="Модель")
    serial_number = models.CharField(max_length=255, blank=True, verbose_name="Серийный номер")
    os_version = models.CharField(max_length=512, blank=True, verbose_name="Версия ПО")
    mac_address = models.CharField(max_length=64, blank=True, verbose_name="MAC адрес")
    sys_name = models.CharField(max_length=255, blank=True, verbose_name="SNMP sysName")
    sys_descr = models.TextField(blank=True, verbose_name="SNMP sysDescr")
    sys_object_id = models.CharField(max_length=255, blank=True, verbose_name="SNMP sysObjectID")
    source = models.CharField(
        max_length=20,
        choices=Source.choices,  # noqa
        default=Source.PING,
        verbose_name="Источник",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,  # noqa
        default=Status.NEW,
        db_index=True,
        verbose_name="Статус",
    )
    confidence = models.PositiveSmallIntegerField(default=0, verbose_name="Confidence")
    detected_protocols = models.JSONField(default=dict, blank=True, verbose_name="Найденные протоколы")
    selected_auth_group = models.ForeignKey(
        AuthGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="discovery_candidates",
        verbose_name="Выбранная группа авторизации",
    )
    selected_snmp_community = models.CharField(
        max_length=64,
        blank=True,
        verbose_name="Выбранный SNMP community",
    )
    device = models.OneToOneField(
        Devices,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="discovery_candidate",
        verbose_name="Созданное оборудование",
    )
    raw_fingerprint = models.JSONField(default=dict, blank=True, verbose_name="Сырой fingerprint")
    last_error = models.TextField(blank=True, verbose_name="Последняя ошибка")
    first_seen_at = models.DateTimeField(auto_now_add=True, verbose_name="Первое обнаружение")
    last_seen_at = models.DateTimeField(auto_now=True, db_index=True, verbose_name="Последнее обнаружение")

    class Meta:
        db_table = "discovery_candidates"
        ordering = ("-last_seen_at", "ip")
        indexes = [
            models.Index(fields=["status", "last_seen_at"], name="disc_cand_status_seen"),
            models.Index(fields=["serial_number"], name="disc_cand_serial"),
        ]
        verbose_name = "Discovery candidate"
        verbose_name_plural = "Discovery candidates"

    def __str__(self) -> str:
        """Вернуть IP и имя кандидата."""

        return f"{self.name or self.ip} ({self.status})"


@receiver(pre_delete, sender=Devices)
def reset_candidate_before_device_delete(sender, instance: Devices, **kwargs) -> None:
    """Вернуть связанного discovery-кандидата в READY перед удалением оборудования."""

    DiscoveryCandidate.objects.filter(
        device=instance,
        status=DiscoveryCandidate.Status.CREATED,
    ).update(status=DiscoveryCandidate.Status.READY)


class DiscoveryAttempt(models.Model):
    """Одна попытка проверки IP адреса во время discovery."""

    class Method(models.TextChoices):
        PING = "PING", "Ping"
        TCP_22 = "TCP_22", "TCP 22"
        TCP_23 = "TCP_23", "TCP 23"
        TCP_161 = "TCP_161", "TCP 161"
        SNMP = "SNMP", "SNMP"
        SSH = "SSH", "SSH"
        TELNET = "TELNET", "Telnet"

    class Status(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"
        TIMEOUT = "TIMEOUT", "Timeout"
        AUTH_FAILED = "AUTH_FAILED", "Auth failed"
        UNSUPPORTED = "UNSUPPORTED", "Unsupported"

    run = models.ForeignKey(
        DiscoveryRun,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Запуск discovery",
    )
    candidate = models.ForeignKey(
        DiscoveryCandidate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attempts",
        verbose_name="Кандидат",
    )
    ip = models.GenericIPAddressField(protocol="ipv4", verbose_name="IP адрес")
    method = models.CharField(max_length=20, choices=Method.choices, verbose_name="Метод")  # noqa
    status = models.CharField(max_length=20, choices=Status.choices, verbose_name="Статус")  # noqa
    duration_ms = models.PositiveIntegerField(default=0, verbose_name="Длительность, мс")
    error = models.TextField(blank=True, verbose_name="Ошибка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        db_table = "discovery_attempts"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["run", "ip"], name="disc_attempt_run_ip"),
            models.Index(fields=["method", "status"], name="disc_attempt_method_status"),
        ]
        verbose_name = "Discovery attempt"
        verbose_name_plural = "Discovery attempts"

    def __str__(self) -> str:
        """Вернуть краткое описание попытки discovery."""

        return f"{self.ip} | {self.method} | {self.status}"
