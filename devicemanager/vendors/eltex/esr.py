from .mes import EltexMES
from ..base.device import BaseDevice
from ..base.validators import validate_and_format_port_as_normal


class EltexESR(EltexMES):
    """
    # Для оборудования от производителя Eltex серия **ESR**

    Проверено для:
     - ESR-12VF
    """

    _template_name = "eltex-esr"

    def _find_system_info(self):
        system = self.send_command("show system")
        self.serialno: str = self.find_or_empty(r"serial number:\s+(\S+)", system)

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
    @validate_and_format_port_as_normal()
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
