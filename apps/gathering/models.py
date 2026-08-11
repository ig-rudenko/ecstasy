from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class GatheringTask(models.Model):
    """Один запуск периодической задачи сбора данных."""

    class Status(models.TextChoices):
        RUNNING = "RUNNING", "Running"
        SUCCESS = "SUCCESS", "Success"
        PARTIAL = "PARTIAL", "Partial"
        FAILURE = "FAILURE", "Failure"

    task_id = models.CharField(max_length=255, unique=True, verbose_name="Celery task ID")
    name = models.CharField(max_length=128, verbose_name="Название задачи")
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.RUNNING,
        db_index=True,
        verbose_name="Статус",
    )
    total_devices = models.PositiveIntegerField(default=0, verbose_name="Всего устройств")
    error_type = models.CharField(max_length=128, blank=True, verbose_name="Тип ошибки")
    error_message = models.TextField(blank=True, verbose_name="Ошибка")
    started_at = models.DateTimeField(default=timezone.now, verbose_name="Дата начала")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата завершения")

    class Meta:
        db_table = "gathering_tasks"
        ordering = ("-started_at",)
        indexes = [
            models.Index(fields=("finished_at",), name="gath_task_finished_idx"),
        ]


class DeviceGatheringResult(models.Model):
    """Результат опроса одного устройства в рамках задачи сбора."""

    class Status(models.TextChoices):
        RUNNING = "RUNNING", "Running"
        SUCCESS = "SUCCESS", "Success"
        SKIPPED = "SKIPPED", "Skipped"
        FAILURE = "FAILURE", "Failure"

    task = models.ForeignKey(GatheringTask, related_name="device_results", on_delete=models.CASCADE)
    device = models.ForeignKey("check.Devices", related_name="gathering_results", on_delete=models.CASCADE)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.RUNNING,
        db_index=True,
        verbose_name="Статус",
    )
    error_type = models.CharField(max_length=128, blank=True, verbose_name="Тип ошибки")
    error_message = models.TextField(blank=True, verbose_name="Ошибка")
    started_at = models.DateTimeField(default=timezone.now, verbose_name="Дата начала")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата завершения")

    class Meta:
        db_table = "device_gathering_results"
        ordering = ("-started_at",)
        constraints = [
            models.UniqueConstraint(fields=("task", "device"), name="uniq_gath_task_device"),
        ]


class MacAddress(models.Model):
    address = models.CharField(max_length=12)
    vlan = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(4096),
        ]
    )
    type = models.CharField(max_length=1)
    device = models.ForeignKey("check.Devices", on_delete=models.CASCADE)
    port = models.CharField(max_length=50)
    desc = models.CharField(max_length=128)
    datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "mac_addresses"
        unique_together = ("address", "device", "port")
        indexes = [
            models.Index(fields=("address",), name="mac_address_index"),
        ]


class Vlan(models.Model):
    vlan = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(4096)])
    desc = models.CharField(max_length=64, blank=True)
    device = models.ForeignKey("check.Devices", on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now=True)  # Обновляется при каждом сохранении

    class Meta:
        db_table = "vlans"
        unique_together = ("vlan", "device")  # Уникальность по двум полям
        indexes = [
            models.Index(fields=("vlan",), name="vlan_index"),
            models.Index(fields=("device", "datetime"), name="vlan_device_dt_index"),
        ]

    def __str__(self):
        return f"{self.device.name} VLAN {self.vlan} - {self.desc}"


class VlanPort(models.Model):
    vlan = models.ForeignKey(Vlan, related_name="ports", on_delete=models.CASCADE)
    port = models.CharField(max_length=50)
    desc = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        db_table = "vlans_ports"
        unique_together = ("vlan", "port")
        indexes = [
            models.Index(fields=("port",), name="vlan_port_index"),
        ]

    def __str__(self):
        return self.port
