import pexpect

from ..base.device import BaseDevice
from ..base.types import DeviceAuthDict


class EltexBase(BaseDevice):
    """
    # Для оборудования от производителя Eltex

    Промежуточный класс, используется, чтобы определить модель оборудования
    """

    prompt = r"\S+#\s*"
    space_prompt = (
        r"More: <space>,  Quit: q or CTRL\+Z, One line: <return> |"
        r"More\? Enter - next line; Space - next page; Q - quit; R - show the rest\."
    )
    vendor = "Eltex"

    def __init__(
            self, session: pexpect, ip: str, auth: DeviceAuthDict, model="", snmp_community: str = ""
    ):
        """
        ## При инициализации смотрим характеристики устройства:

            # show system

          - MAC
          - Модель

        В зависимости от модели можно будет понять, какой класс для Eltex использовать далее

        :param session: Это объект сеанса pexpect c установленной сессией оборудования
        :param ip: IP-адрес устройства, к которому вы подключаетесь
        :param auth: словарь, содержащий имя пользователя и пароль для устройства
        :param model: Модель коммутатора
        """

        super().__init__(session, ip, auth, model, snmp_community)
        # Получение системной информации с устройства.
        system = self.send_command("show system")
        # Нахождение MAC-адреса устройства.
        self.mac = self.find_or_empty(r"System MAC [Aa]ddress:\s+(\S+)", system)
        # Регулярное выражение, которое ищет модель устройства.
        model = self.find_or_empty(
            r"System Description:\s+(\S+)|System type:\s+Eltex (\S+)", system
        )
        self.model = model[0] or model[1] if model else ""

    def save_config(self):
        pass

    def get_mac(self, port) -> list:
        return []

    def get_interfaces(self) -> list:
        return []

    def get_vlans(self) -> list:
        return []

    def reload_port(self, port: str, save_config=True) -> str:
        return ""

    def set_port(self, port: str, status: str, save_config=True) -> str:
        return ""

    def set_description(self, port: str, desc: str) -> str:
        return ""

    def get_port_info(self, port: str) -> dict:
        return {}

    def get_port_type(self, port: str) -> str:
        return ""

    def get_port_config(self, port: str) -> str:
        return ""

    def get_port_errors(self, port: str) -> str:
        return ""

    def get_device_info(self) -> dict:
        return {}
