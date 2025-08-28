import re

from .base import EltexBase
from .esr import EltexESR
from .ltp_16n import EltexLTP16N
from .ltp_4x_8x import EltexLTP
from .mes import EltexMES
from ..base.device import BaseDevice
from ..base.factory import AbstractDeviceFactory

__all__ = ["EltexFactory"]

from ..base.types import DeviceAuthDict

from ... import UnknownDeviceError


class EltexFactory(AbstractDeviceFactory):
    @staticmethod
    def is_can_use_this_factory(session=None, version_output=None) -> bool:
        return version_output and bool(
            re.search(r"Eltex LTP|Active-image:|Boot version:", str(version_output))
        )

    @classmethod
    def get_device(
        cls, session, ip: str, snmp_community: str, auth: DeviceAuthDict, version_output: str = ""
    ) -> BaseDevice:
        version_output = str(version_output)

        if "Eltex LTP" in version_output:
            model = BaseDevice.find_or_empty(r"Eltex (\S+[^:\s])", version_output)
            if re.match(r"LTP-[48]X", model):
                device = EltexLTP(session, ip, auth, model=model, snmp_community=snmp_community)
                device.os_version = device.find_or_empty("software version (.+)", version_output).strip()
                return device
            if "LTP-16N" in model:
                device = EltexLTP16N(session, ip, auth, model=model, snmp_community=snmp_community)
                device.os_version = device.find_or_empty("software version (.+)", version_output).strip()
                return device

        # Eltex MES, ESR
        if re.search(r"Active-image:|Boot version:", version_output):
            eltex_device = EltexBase(session, ip, auth)
            if "MES" in eltex_device.model:
                device = EltexMES(
                    eltex_device.session,
                    ip,
                    auth,
                    model=eltex_device.model,
                    mac=eltex_device.mac,
                    snmp_community=snmp_community,
                )
                os_version = device.find_or_empty(r"Version: (\S+)", version_output)
                build = device.find_or_empty(r"Build: (.+)", version_output).strip()
                date = device.find_or_empty(r"Date: (\S+)", version_output)
                device.os_version = f"Version: {os_version} Build: {build} {date}"
                return device

            if "ESR" in eltex_device.model:
                device = EltexESR(
                    eltex_device.session,
                    ip,
                    auth,
                    model=eltex_device.model,
                    mac=eltex_device.mac,
                    snmp_community=snmp_community,
                )
                device.os_version = device.find_or_empty(
                    "SW version:(.+)HW version", version_output, flags=re.DOTALL
                ).strip()
                return device

        raise UnknownDeviceError("EltexFactory не удалось распознать модель оборудования", ip=ip)
