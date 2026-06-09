import re

from devicemanager import UnknownDeviceError
from devicemanager.vendors import BaseDevice
from devicemanager.vendors.base.factory import AbstractDeviceFactory
from devicemanager.vendors.base.types import DeviceAuthDict

from .snr_s29xx import SNRS29XX
from .snr_s52xx import SNRS52XX


class SNRFactory(AbstractDeviceFactory):
    @staticmethod
    def support_devices() -> list[type[BaseDevice]]:
        return [SNRS52XX, SNRS29XX]

    @staticmethod
    def is_can_use_this_factory(session=None, version_output=None) -> bool:
        return version_output and "SNR" in version_output or "eNOS software" in version_output

    @classmethod
    def get_device(
        cls,
        session,
        ip: str,
        snmp_community: str,
        auth: DeviceAuthDict,
        version_output: str = "",
    ) -> BaseDevice:
        model = BaseDevice.find_or_empty(r"SNR-\S+", version_output)
        serialno = BaseDevice.find_or_empty(r"Serial No.:\s*(\S+)", version_output)
        mac = BaseDevice.find_or_empty(r"Vlan MAC (\S+)", version_output)

        if re.search(r"SNR-S52\d\d", model):
            dev = SNRS52XX(session, ip, auth, model=model, snmp_community=snmp_community)
            dev.serialno = serialno
            dev.mac = mac
            return dev

        if re.search(r"SNR-S29\d\d", model):
            dev = SNRS29XX(session, ip, auth, model=model)
            dev.serialno = serialno
            dev.mac = mac
            return dev

        raise UnknownDeviceError(f"SNRFactory не удалось распознать модель оборудования: {model}", ip=ip)
