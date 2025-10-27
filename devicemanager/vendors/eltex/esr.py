import io

from ..base.device import BaseDevice
from ..base.types import DeviceAuthDict
from ..base.validators import validate_and_format_port_as_normal
from .mes import EltexMES


class EltexESR(EltexMES):
    """
    # Для оборудования от производителя Eltex серия **ESR**

    Проверено для:
     - ESR-12VF
    """

    _template_name = "eltex-esr"

    def __init__(
        self,
        session,
        ip: str,
        auth: DeviceAuthDict,
        model: str = "",
        snmp_community: str = "",
        mac: str = "",
    ):
        super().__init__(session, ip, auth, model, snmp_community)
        self.mac = mac
        self._find_system_info()
        self.send_command("terminal datadump")  # Убираем постраничный вывод

    def _find_system_info(self) -> None:
        system = self.send_command("show system")
        self.serialno: str = self.find_or_empty(r"serial number:\s+(\S+)", system)

    def send_command(
        self,
        command: str,
        before_catch: str | None = None,
        expect_command=True,
        num_of_expect=10,
        space_prompt=None,
        prompt=None,
        pages_limit=None,
        command_linesep="\n",
        timeout=10,
    ) -> str:
        return super().send_command(
            command=command,
            before_catch=before_catch,
            expect_command=False,
            num_of_expect=num_of_expect,
            space_prompt=space_prompt,
            prompt=prompt,
            pages_limit=pages_limit,
            command_linesep=command_linesep,
            timeout=timeout,
        )

    @BaseDevice.lock_session
    def save_config(self):
        """
        ## Сохраняем конфигурацию оборудования

        Для ESR необходимо сделать коммит конфигурации, а затем подтвердить её

            # commit
            # confirm

        Ожидаем ответа от оборудования **Configuration has been confirmed**,
        если нет, то ошибка сохранения
        """

        self.session.sendline("commit")
        if (
            self.session.expect(
                [
                    self.prompt,  # 0
                    "Configuration has been successfully applied",  # 1
                    "Unknown command",  # 2
                ]
            )
            == 2  # Если неверная команда
        ):
            # Выходим из режима редактирования конфигурации
            self.session.sendline("end")
            self.session.sendline("commit")
            self.session.expect([self.prompt, "Configuration has been successfully applied"])

        # Подтверждаем изменение
        status = self.send_command("confirm")
        if "Configuration has been confirmed" in status:
            return self.SAVED_OK
        return self.SAVED_ERR

    @BaseDevice.lock_session
    @validate_and_format_port_as_normal()
    def port_type(self, port: str) -> str:
        """
        ## Возвращает тип порта

        Используется команда:

            # show interfaces sfp

        :param port: Порт для проверки
        :return: "SFP" или "COPPER"
        """

        if "SFP present" in self.send_command(f"show interfaces sfp {port}"):
            return "SFP"
        return "COPPER"

    @BaseDevice.lock_session
    @validate_and_format_port_as_normal({"type": "error", "data": "Неверный порт"})
    def get_port_info(self, port: str) -> dict:
        """
        ## Возвращаем информацию о порте.

        Через команду:

            # show interfaces status {port}

        :param port: Номер порта, для которого требуется получить информацию
        """

        info = self.send_command(
            f"show interfaces status {port}",
            expect_command=False,
            before_catch=r"Description:.+",
        )
        return {
            "type": "text",
            "data": info,
        }

    @BaseDevice.lock_session
    @validate_and_format_port_as_normal()
    def get_port_errors(self, port: str) -> str:
        """
        ## Выводим ошибки на порту

        Используется команда:

            # show interfaces counters

        :param port: Порт для проверки на наличие ошибок
        """

        port_stat = self.send_command(f"show interfaces counters {port}").split("\n")

        errors = ""
        for line in port_stat:
            if "errors" in line:
                errors += line.strip() + "\n"
        return errors

    def get_device_info(self) -> dict:
        return {}

    @BaseDevice.lock_session
    def get_current_configuration(self) -> io.BytesIO:
        config = self.send_command("show running-config", expect_command=True)
        config = config.strip()
        return io.BytesIO(config.encode())
