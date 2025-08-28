import re

import pexpect

from .ce6865 import HuaweiCE6865
from .cx600 import HuaweiCX600
from .ma5600 import HuaweiMA5600T
from .quidway import BaseDevice, Huawei
from ..base.factory import AbstractDeviceFactory
from ..base.types import DeviceAuthDict
from ... import UnknownDeviceError

__all__ = ["HuaweiFactory"]


class HuaweiFactory(AbstractDeviceFactory):
    @staticmethod
    def is_can_use_this_factory(session=None, version_output=None) -> bool:
        return bool(
            version_output and re.search(r"Unrecognized command|% Unknown command", str(version_output))
        )

    @classmethod
    def get_device(
        cls,
        session,
        ip: str,
        snmp_community: str,
        auth: DeviceAuthDict,
        version_output: str = "",
    ) -> BaseDevice:
        if "Unrecognized command" in version_output:
            version = cls.send_command(session, "display version")
            if "CX600" in version:
                model = BaseDevice.find_or_empty(r"HUAWEI (\S+) uptime", version, flags=re.IGNORECASE)
                return HuaweiCX600(session, ip, auth, model, snmp_community)

            elif "quidway" in version.lower():
                return Huawei(session, ip, auth, snmp_community=snmp_community)

            elif "ce6865" in version.lower():
                model = BaseDevice.find_or_empty(r"HUAWEI (\S+) uptime is", version)
                device = HuaweiCE6865(session, ip, auth, snmp_community=snmp_community, model=model)
                device.os_version = device.find_or_empty("software, (Version .+)", version).strip()
                return device

            # Если снова 'Unrecognized command', значит недостаточно прав, пробуем Huawei
            if "Unrecognized command" in version:
                return Huawei(session, ip, auth, snmp_community=snmp_community)

        # HuaweiMA5600T
        if "% Unknown command" in version_output:
            version_output = ""
            session.sendline("display version")
            while True:
                match = session.expect([r"]$", "---- More", r">$", r"#", pexpect.TIMEOUT, "{"])
                if match == 5:
                    session.expect(r"\}:")
                    session.sendline("\n")
                    continue
                version_output += str(session.before.decode("utf-8"))
                if match == 1:
                    session.sendline(" ")
                elif match == 4:
                    session.sendcontrol("C")
                else:
                    break
            if re.findall(r"PRODUCT\s*:? MA5600", version_output):
                device = HuaweiMA5600T(session, ip, auth, model="MA5600T", snmp_community=snmp_community)
                os_version = device.find_or_empty(r"VERSION\s*:?\s*(MA5600\S+)", version_output)
                patch = device.find_or_empty("PATCH : (\S+)", version_output)
                if os_version or patch:
                    device.os_version = f"Version: {os_version} Patch: {patch}"
                return device

        raise UnknownDeviceError("HuaweiFactory не удалось распознать модель оборудования", ip=ip)
