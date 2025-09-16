from concurrent.futures import ThreadPoolExecutor
from typing import TypedDict

from django.contrib.auth.base_user import AbstractBaseUser

from check.logging import log
from check.models import Bras, Devices
from devicemanager.exceptions import BaseDeviceException


class BrasSession(TypedDict):
    session: str | None
    errors: list[str]


def get_bras_sessions(mac: str) -> dict[str, BrasSession]:
    """Возвращает словарь сессий на оборудовании BRAS по MAC адресу."""

    result: dict[str, BrasSession] = {}

    with ThreadPoolExecutor() as executor:
        for bras in Bras.objects.all():
            # Приведенный выше код создает пул потоков,
            # а затем отправляет функцию get_user_session в пул потоков.
            executor.submit(get_bras_user_session, bras, mac, result)
    return result


def get_bras_user_session(bras: Bras, mac: str, result: dict[str, BrasSession]):
    """
    ## Получает сеанс пользователя для заданного MAC-адреса.

    :param bras: Объект Bras, к которому подключается пользователь
    :param mac: MAC адрес пользователя
    :param result: dict, содержащий информацию сессий.
    """

    result[bras.name] = {"session": None, "errors": []}

    try:
        result[bras.name]["session"] = bras.connect().get_access_user_data(mac)
    except BaseDeviceException as exc:
        result[bras.name]["errors"].append(exc.message)


def cut_bras_session(device: Devices | None, user: AbstractBaseUser, mac: str, port: str) -> dict:
    """
    Cut bras session
    """

    # Словарь, который будет содержать данные для отправки
    result: dict = {"errors": [], "portReloadStatus": "SKIP"}

    for bras in Bras.objects.all():
        bras.connect().cut_access_user_session(mac)
        log(user, bras, f"cut access-user mac-address {mac}")

    if device is None:
        return result

    try:
        # Перезагружаем порт без сохранения конфигурации
        reload_port_status = device.connect().reload_port(port, save_config=False)
        result["portReloadStatus"] = reload_port_status  # Успех

        # Логи
        log(user, device, f"reload port {port} \n{reload_port_status}")

    except BaseDeviceException as e:
        result["errors"].append(f"Сессия сброшена, но порт не был перезагружен! {e}")

    return result
