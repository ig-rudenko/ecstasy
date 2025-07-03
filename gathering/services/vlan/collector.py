from datetime import timedelta

import orjson
from django.conf import settings
from django.utils import timezone

from app_settings.models import ZabbixConfig
from check.models import Devices
from devicemanager.dc import DeviceRemoteConnector
from devicemanager.device import DeviceManager, zabbix_api, Interfaces
from devicemanager.exceptions import BaseDeviceException
from devicemanager.vendors.base.types import VlanTableType  # Updated to handle VLANs
from gathering.models import Vlan, VlanPort  # Updated model for VLANs
from net_tools.models import DevicesInfo


class VlanTableGather:
    """
    # This class is used for collecting VLAN information from the device
    """

    def __init__(self, from_: Devices):
        if not zabbix_api.zabbix_url:
            zabbix_api.set_lazy_attributes(ZabbixConfig.load())

        self.device: Devices = from_
        self.table: VlanTableType = []  # To hold the VLAN table
        self.interfaces: Interfaces = Interfaces()
        self.interfaces_desc: dict = {}

        try:
            # Create a session with the device and ensure proper closure after usage
            with DeviceRemoteConnector(
                ip=self.device.ip,
                protocol=self.device.port_scan_protocol,
                auth_obj=self.device.auth_group,
                snmp_community=self.device.snmp_community or "",
            ) as session:
                if hasattr(session, "normalize_interface_name"):
                    self.normalize_interface = session.normalize_interface_name

                # Fetching interfaces and descriptions from the device
                self.interfaces = self.get_interfaces()
                self.interfaces_desc = self.format_interfaces(self.interfaces)

                # Gather VLAN information from the device
                self.table = self.get_vlan_table(session)

            # Save interfaces to the database
            self.save_interfaces()

        except BaseDeviceException:
            pass

    @staticmethod
    def get_vlan_table(session) -> VlanTableType:
        """
        # Fetch the VLAN table from the device session. If a specific method exists for VLANs, call it.
        """
        if hasattr(session, "get_vlan_table"):
            return session.get_vlan_table() or []
        return []

    def get_interfaces(self) -> Interfaces:
        device_manager = DeviceManager.from_model(self.device)
        device_manager.collect_interfaces(vlans=False, current_status=True, make_session_global=False)
        return device_manager.interfaces or Interfaces()

    def format_interfaces(self, old_interfaces: Interfaces) -> dict:
        """
        # Converts a list of interfaces into a dictionary with interface names as keys and their descriptions as values.
        """
        interfaces = {}
        for line in old_interfaces:
            normal_interface = self.normalize_interface(line.name)
            if normal_interface:
                interfaces[normal_interface] = line.desc
        return interfaces

    def save_interfaces(self) -> None:
        """
        # Saves the interface information to the database.
        """
        if not self.interfaces:
            return

        interfaces_to_save = [
            {
                "Interface": line.name,
                "Status": line.status,
                "Description": line.desc,
            }
            for line in self.interfaces
        ]

        try:
            device_history = DevicesInfo.objects.get(dev_id=self.device.id)
        except DevicesInfo.DoesNotExist:
            device_history = DevicesInfo.objects.create(dev=self.device)

        device_history.interfaces = orjson.dumps(interfaces_to_save).decode()
        device_history.interfaces_date = timezone.now()
        device_history.save(update_fields=["interfaces", "interfaces_date"])

    def save_vlan_info(self) -> int:
        if not self.table:
            return 0

        for vlan, port, vlan_desc in self.table:
            vlan_obj, created = Vlan.objects.get_or_create(
                vlan=vlan,
                device=self.device,
                defaults={"desc": vlan_desc},
            )
            if not created:
                vlan_obj.desc = vlan_desc
                vlan_obj.save()

            VlanPort.objects.update_or_create(
                vlan=vlan_obj,
                port=port,
                defaults={"desc": ""},
            )
        return len(self.table)

    def clear_old_records(self, timedelta_=timedelta(hours=48)) -> None:
        old_vlans = Vlan.objects.filter(
            device=self.device,
            datetime__lt=timezone.now() - timedelta_,
        )
        VlanPort.objects.filter(vlan__in=old_vlans).delete()
        old_vlans.delete()

    @property
    def bulk_options(self) -> dict:
        """
        # Returns options for bulk_create depending on the database configuration.
        """
        options = {
            "update_conflicts": True,
            "update_fields": ["vlan", "type", "datetime", "desc"],
            "batch_size": 999,
        }

        database_engine = str(settings.DATABASES["default"]["ENGINE"]).rsplit(".", 1)[1]
        if database_engine in ["postgresql", "sqlite3"]:
            options["unique_fields"] = ["vlan", "device"]

        return options

    def bulk_create(self) -> int:
        """
        # Creates or updates VLAN entries in the database.
        """
        return self.save_vlan_info()
