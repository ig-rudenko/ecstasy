import re

import pexpect

from .ce6865 import HuaweiCE6865
from .cx600 import HuaweiCX600
from .ma5600 import HuaweiMA5600T
from .quidway import BaseDevice, Huawei
from ..base.factory import AbstractDeviceFactory
from ... import UnknownDeviceError


__all__ = ["HuaweiFactory"]


class HuaweiFactory(AbstractDeviceFactory):
    @staticmethod
    def is_can_use_this_factory(session=None, version_output=None) -> bool:
        return version_output and re.match(
            r"Unrecognized command|% Unknown command", str(version_output)
        )

    @classmethod
    def get_device(
        cls, session, ip: str, snmp_community: str, auth_obj, version_output: str = ""
    ) -> BaseDevice:
        version = cls.send_command(session, "display version")
        if "huawei" in version.lower():
            if "CX600" in version:
                model = BaseDevice.find_or_empty(
                    r"HUAWEI (\S+) uptime", version, flags=re.IGNORECASE
                )
                return HuaweiCX600(session, ip, auth_obj, model, snmp_community)

            elif "quidway" in version.lower():
                return Huawei(session, ip, auth_obj, snmp_community=snmp_community)

            elif "ce6865" in version.lower():
                model = BaseDevice.find_or_empty(r"HUAWEI (\S+) uptime is", version)
                return HuaweiCE6865(
                    session, ip, auth_obj, snmp_community=snmp_community, model=model
                )

        # Если снова 'Unrecognized command', значит недостаточно прав, пробуем Huawei
        if "Unrecognized command" in version:
            return Huawei(session, ip, auth_obj, snmp_community=snmp_community)

        # HuaweiMA5600T
        if "% Unknown command" in version:
            session.sendline("display version")
            while True:
                match = session.expect([r"]$", "---- More", r">$", r"#", pexpect.TIMEOUT, "{"])
                if match == 5:
                    session.expect(r"\}:")
                    session.sendline("\n")
                    continue
                version += str(session.before.decode("utf-8"))
                if match == 1:
                    session.sendline(" ")
                elif match == 4:
                    session.sendcontrol("C")
                else:
                    break
            if re.findall(r"VERSION : MA5600", version):
                model = BaseDevice.find_or_empty(r"VERSION : (MA5600\S+)", version)
                return HuaweiMA5600T(
                    session, ip, auth_obj, model=model, snmp_community=snmp_community
                )

        raise UnknownDeviceError("HuaweiFactory не удалось распознать модель оборудования", ip=ip)
