from . import UnknownDeviceError
from .vendors.base.device import BaseDevice
from .vendors.base.factory import AbstractDeviceFactory
from .vendors.base.types import DeviceAuthDict
from .vendors.cisco import CiscoFactory
from .vendors.dlink import DlinkFactory
from .vendors.edge_core import EdgeCoreFactory
from .vendors.eltex.factory import EltexFactory
from .vendors.extreme import ExtremeFactory
from .vendors.huawei.factory import HuaweiFactory
from .vendors.iskratel import IskratelFactory
from .vendors.juniper import JuniperFactory
from .vendors.mikrotik import MikrotikFactory
from .vendors.procurve import ProCurveFactory
from .vendors.qtech import QtechFactory
from .vendors.zte import ZTEFactory


class DeviceMultiFactory(AbstractDeviceFactory):
    @staticmethod
    def is_can_use_this_factory(session=None, version_output=None) -> bool:
        return True

    @classmethod
    def get_device(
            cls, session, ip: str, snmp_community: str, auth: DeviceAuthDict, version_output: str = ""
    ) -> BaseDevice:
        """
        # После подключения динамически определяем вендора оборудования и его модель

        Отправляем команду:

            # show version

        Ищем в выводе команды строчки, которые указывают на определенный вендор

        |           Вендор            |     Строка для определения    |
        |:----------------------------|:------------------------------|
        |             ZTE             |      " ZTE Corporation:"      |
        |           Huawei            |     "Unrecognized command"    |
        |            Cisco            |           "cisco"             |
        |          D-Link             |  "Next possible completions:" |
        |          Edge-Core          |      "Hardware version"       |
        |          Extreme            |          "ExtremeXOS"         |
        |           Q-Tech            |            "QTECH"            |
        |          Iskratel           |   "ISKRATEL" или "IskraTEL"   |
        |           Juniper           |            "JUNOS"            |
        |          ProCurve           |         "Image stamp:"        |

        """

        version_output += cls.send_command(session, "show version")

        if "bad command name show" in version_output:
            version_output = cls.send_command(session, "system resource print")

        factory_data = {
            "session": session,
            "ip": ip,
            "snmp_community": snmp_community,
            "auth": auth,
            "version_output": version_output,
        }

        factories = [
            HuaweiFactory,
            DlinkFactory,
            EltexFactory,
            CiscoFactory,
            IskratelFactory,
            ExtremeFactory,
            MikrotikFactory,
            QtechFactory,
            ZTEFactory,
            EdgeCoreFactory,
            JuniperFactory,
            ProCurveFactory,
        ]

        for factory in factories:
            if factory.is_can_use_this_factory(session=session, version_output=version_output):
                return factory.get_device(**factory_data)

        raise UnknownDeviceError("Модель оборудования не была распознана", ip=ip)
