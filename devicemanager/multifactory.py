from . import UnknownDeviceError
from .vendors.base.device import BaseDevice
from .vendors.base.factory import AbstractDeviceFactory
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
        cls, session, ip: str, snmp_community: str, auth_obj, version_output: str = ""
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

        version = cls.send_command(session, "show version")

        if "bad command name show" in version:
            version = cls.send_command(session, "system resource print")

        factory_data = {
            "session": session,
            "ip": ip,
            "snmp_community": snmp_community,
            "auth_obj": auth_obj,
            "version_output": version,
        }

        if MikrotikFactory.is_can_use_this_factory(version_output=version):
            return MikrotikFactory.get_device(**factory_data)

        if ProCurveFactory.is_can_use_this_factory(version_output=version):
            return ProCurveFactory.get_device(**factory_data)

        if ZTEFactory.is_can_use_this_factory(version_output=version):
            return ZTEFactory.get_device(**factory_data)

        if HuaweiFactory.is_can_use_this_factory(version_output=version):
            return HuaweiFactory.get_device(**factory_data)

        if CiscoFactory.is_can_use_this_factory(version_output=version):
            return CiscoFactory.get_device(**factory_data)

        if DlinkFactory.is_can_use_this_factory(version_output=version):
            return DlinkFactory.get_device(**factory_data)

        if EdgeCoreFactory.is_can_use_this_factory(version_output=version):
            return EdgeCoreFactory.get_device(**factory_data)

        if EltexFactory.is_can_use_this_factory(version_output=version):
            return EltexFactory.get_device(**factory_data)

        if ExtremeFactory.is_can_use_this_factory(version_output=version):
            return ExtremeFactory.get_device(**factory_data)

        if QtechFactory.is_can_use_this_factory(version_output=version):
            return QtechFactory.get_device(**factory_data)

        if IskratelFactory.is_can_use_this_factory(version_output=version):
            return IskratelFactory.get_device(**factory_data)

        if JuniperFactory.is_can_use_this_factory(version_output=version):
            return JuniperFactory.get_device(**factory_data)

        raise UnknownDeviceError("Модель оборудования не была распознана", ip=ip)
