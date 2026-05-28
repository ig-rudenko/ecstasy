import re

from .. import BaseDevice
from ..base.factory import AbstractDeviceFactory
from ..base.types import DeviceAuthDict
from .basic import Cisco
from .nexus import CiscoNexus


class CiscoFactory(AbstractDeviceFactory):
    @staticmethod
    def support_devices() -> list[type[BaseDevice]]:
        return [Cisco, CiscoNexus]

    @staticmethod
    def is_can_use_this_factory(session=None, version_output=None) -> bool:
        return version_output and "cisco" in str(version_output).lower()

    @classmethod
    def get_device(
        cls,
        session,
        ip: str,
        snmp_community: str,
        auth: DeviceAuthDict,
        version_output: str = "",
    ) -> BaseDevice:

        if "Cisco Nexus" in version_output:
            return CiscoNexus(session, ip, auth, snmp_community)

        model = BaseDevice.find_or_empty(r"Model number\s*:\s*(\S+)", version_output)
        mac = Cisco.find_or_empty(r"[MACmac] [Aa]ddress\s+: (\S+)", version_output)
        os_version = Cisco.find_or_empty(r"(Version \S+),.+Copyright", version_output, flags=re.DOTALL)

        device = Cisco(session, ip, auth, model=model, snmp_community=snmp_community)

        device.mac = mac
        device.os_version = os_version

        return device
