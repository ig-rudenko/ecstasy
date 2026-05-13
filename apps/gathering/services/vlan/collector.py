from collections import defaultdict

from django.db import transaction
from django.utils import timezone

from apps.gathering.models import Vlan, VlanPort
from devicemanager.remote.exceptions import InvalidMethod
from devicemanager.vendors.base.types import VlanTableType

from ..collectors import AbstractRealtimeCollector


class VlanTableGather(AbstractRealtimeCollector):
    """
    # This class is used for collecting VLAN information from the device
    """

    def collect(self) -> None:
        table = self._get_vlan_table()
        self._save_vlan_info(table)

    def _get_vlan_table(self) -> VlanTableType:
        """
        # Fetch the VLAN table from the device session. If a specific method exists for VLANs, call it.
        """
        try:
            if hasattr(self.session, "get_vlan_table"):
                return self.session.get_vlan_table() or []
        except InvalidMethod:
            pass
        return []

    def _save_vlan_info(self, table: VlanTableType) -> int:
        """Save collected VLANs and their ports using one row per VLAN port."""
        if not table:
            return 0

        now = timezone.now()
        vlan_descriptions: dict[int, str] = {}
        vlan_ports: dict[int, set[str]] = defaultdict(set)

        for vlan, ports, vlan_desc in table:
            vlan_descriptions[vlan] = vlan_desc or ""
            for port in ports:
                normalized_port = self.normalize_interface(port) or port
                vlan_ports[vlan].add(normalized_port)

        vlan_ids = set(vlan_descriptions)
        with transaction.atomic():
            existing_vlans = {
                obj.vlan: obj
                for obj in Vlan.objects.select_for_update().filter(device=self.device, vlan__in=vlan_ids)
            }
            missing_vlans = [
                Vlan(vlan=vlan, device=self.device, desc=desc, datetime=now)
                for vlan, desc in vlan_descriptions.items()
                if vlan not in existing_vlans
            ]
            if missing_vlans:
                Vlan.objects.bulk_create(missing_vlans, batch_size=999)

            vlans_to_update = []
            for vlan, vlan_obj in existing_vlans.items():
                vlan_obj.desc = vlan_descriptions[vlan]
                vlan_obj.datetime = now
                vlans_to_update.append(vlan_obj)

            if vlans_to_update:
                Vlan.objects.bulk_update(vlans_to_update, ["desc", "datetime"], batch_size=999)

            Vlan.objects.filter(device=self.device).exclude(vlan__in=vlan_ids).delete()
            saved_vlans = {
                obj.vlan: obj for obj in Vlan.objects.filter(device=self.device, vlan__in=vlan_ids)
            }

            desired_ports = {
                (saved_vlans[vlan].id, port): self.interfaces_desc.get(port, "")
                for vlan, ports in vlan_ports.items()
                for port in ports
                if vlan in saved_vlans
            }
            existing_ports = {
                (obj.vlan_id, obj.port): obj
                for obj in VlanPort.objects.filter(vlan_id__in=[obj.id for obj in saved_vlans.values()])
            }

            ports_to_create = [
                VlanPort(vlan_id=vlan_id, port=port, desc=desc)
                for (vlan_id, port), desc in desired_ports.items()
                if (vlan_id, port) not in existing_ports
            ]
            ports_to_update = []
            for key, port_obj in existing_ports.items():
                if key in desired_ports:
                    desc = desired_ports[key]
                    if port_obj.desc != desc:
                        port_obj.desc = desc
                        ports_to_update.append(port_obj)

            stale_port_ids = [
                port_obj.id for key, port_obj in existing_ports.items() if key not in desired_ports
            ]
            if stale_port_ids:
                VlanPort.objects.filter(id__in=stale_port_ids).delete()
            if ports_to_create:
                VlanPort.objects.bulk_create(ports_to_create, batch_size=999)
            if ports_to_update:
                VlanPort.objects.bulk_update(ports_to_update, ["desc"], batch_size=999)

        return len(desired_ports)
