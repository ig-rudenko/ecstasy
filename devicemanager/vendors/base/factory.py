from abc import ABC, abstractmethod

import pexpect

from .device import BaseDevice
from .types import DeviceAuthDict


class AbstractDeviceFactory(ABC):
    @classmethod
    @abstractmethod
    def get_device(
        cls, session, ip: str, snmp_community: str, auth: DeviceAuthDict, version_output: str = ""
    ) -> BaseDevice:
        pass

    @staticmethod
    @abstractmethod
    def is_can_use_this_factory(session=None, version_output=None) -> bool:
        pass

    @staticmethod
    def send_command(session, command: str) -> str:
        """
        # Простой метод для отправки команды с постраничной записью вывода результата
        """

        session.send(command + "\r")
        version = ""
        while True:
            match = session.expect(
                [
                    r"[#>\]]\s*$|[#>\]]\s*\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])|\x08$",  # 0
                    r"-More-|-+\(more.*?\)-+",  # 1
                    pexpect.TIMEOUT,  # 2
                ],
                timeout=3,
            )

            version += str(session.before.decode("utf-8"))
            if match == 1:
                session.send(" ")
            elif match == 2:
                session.sendcontrol("C")
            else:
                break
        return version
