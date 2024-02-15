from typing import Sequence

import orjson
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from check.models import Devices
from devicemanager.device import Interfaces


class DevicesInfo(models.Model):
    dev = models.OneToOneField(Devices, primary_key=True, on_delete=models.CASCADE)
    interfaces = models.TextField(null=True)
    interfaces_date = models.DateTimeField(null=True)
    vlans = models.TextField(null=True)
    vlans_date = models.DateTimeField(null=True)

    class Meta:
        db_table = "device_info"

    def update_interfaces_state(self, interfaces: Sequence | Interfaces):
        """
        Обновляет поле интерфейсов и время.
        """
        self.interfaces = self._parse_interfaces_to_json(interfaces, with_vlans=False)
        self.interfaces_date = timezone.now()

    def update_interfaces_with_vlans_state(self, interfaces: Sequence | Interfaces):
        """
        Обновляет поле интерфейсов и вланов, а также время
        """
        self.vlans = self._parse_interfaces_to_json(interfaces, with_vlans=True)
        self.vlans_date = timezone.now()

    @staticmethod
    def _parse_interfaces_to_json(interfaces: Sequence | Interfaces, with_vlans: bool) -> str:
        if isinstance(interfaces, Sequence):
            interfaces = Interfaces(interfaces)

        def get_intf_dict(interface) -> dict:
            if with_vlans:
                res = {
                    "Interface": interface.name,
                    "Status": interface.status,
                    "Description": interface.desc.strip(),
                    "VLAN's": interface.vlan,
                }
            else:
                res = {
                    "Interface": interface.name,
                    "Status": interface.status,
                    "Description": interface.desc.strip(),
                }
            return res

        interfaces_list = [get_intf_dict(line) for line in interfaces]
        return orjson.dumps(interfaces_list).decode()


class DescNameFormat(models.Model):
    standard = models.CharField(max_length=255, unique=True, verbose_name="Необходимое имя оборудования")
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
    name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Название")
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
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name="Описание")
