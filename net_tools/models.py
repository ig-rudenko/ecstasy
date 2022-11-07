from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from check.models import Devices


class DevicesInfo(models.Model):
    ip = models.CharField(max_length=15, primary_key=True, null=False)
    interfaces = models.TextField(null=True)
    interfaces_date = models.DateTimeField(null=True)
    sys_info = models.TextField(null=True)
    sys_info_date = models.DateTimeField(null=True)
    vlans = models.TextField(null=True)
    vlans_date = models.DateTimeField(null=True)
    device_name = models.CharField(max_length=100, null=True, unique=True)

    class Meta:
        db_table = "device_info"
        ordering = ("ip",)


class DescNameFormat(models.Model):
    standard = models.CharField(
        max_length=255, unique=True, verbose_name="Необходимое имя оборудования"
    )
    replacement = models.TextField(verbose_name="Возможные варианты (через запятую)")

    class Meta:
        db_table = "vlan_traceroute_desc_name_format"
        verbose_name = "VLAN traceroute desc name format"


class VlanName(models.Model):
    vid = models.PositiveIntegerField(
        primary_key=True,
        verbose_name="VLAN id",
        validators=[MinValueValidator(1), MaxValueValidator(4096)],
    )
    name = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Название"
    )
    description = models.TextField(verbose_name="Описание")

    def __str__(self):
        return f"{self.vid} ({self.name})"

    class Meta:
        db_table = "vlan_name"


class DevicesForMacSearch(models.Model):
    device = models.ForeignKey(
        Devices,
        on_delete=models.CASCADE,
        verbose_name="Оборудование для поиска MAC",
        help_text="Будет искать MAC в таблице arp оборудования",
    )
    description = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Описание"
    )
