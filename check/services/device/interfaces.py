import re
from typing import Any

import orjson
from django.contrib.auth.models import User
from rest_framework.exceptions import PermissionDenied, ValidationError, APIException

from check import models
from check.logging import log
from check.models import Profile
from devicemanager.device import Interfaces
from devicemanager.device.interfaces import Interface
from devicemanager.vendors.base.types import SetDescriptionResult
from net_tools.models import DevicesInfo, VlanName


def check_user_interface_permission(
    user: User, device: models.Devices, interface_name: str, action: str = ""
) -> Interface:
    """
    Проверка прав доступа к интерфейсу.
    :param user: Пользователь.
    :param device: Устройство.
    :param interface_name: Имя интерфейса.
    :param action: Действие над интерфейсом ("up", "down", "reload"). Необязательно.
    :return: Интерфейс.

    :raises PermissionDenied: Если пользователь не имеет прав на выполнение данного действия (или нет профиля).
    :raises ValidationError: Если интерфейс не найден.
    """

    try:
        profile: Profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        raise PermissionDenied(detail="У вас нет профиля для выполнения данного действия!")

    # Смотрим интерфейсы, которые сохранены в БД
    dev_info, _ = DevicesInfo.objects.get_or_create(dev=device)

    if dev_info.interfaces is None:
        # Собираем интерфейсы с оборудования.
        interfaces = Interfaces(device.connect().get_interfaces())
    else:
        # Преобразовываем JSON строку с интерфейсами в класс `Interfaces`
        interfaces = Interfaces(orjson.loads(dev_info.interfaces))

    # Далее смотрим описание на порту, так как от этого будет зависеть, может ли пользователь управлять им
    interface = interfaces[interface_name]

    if not interface.name:
        raise ValidationError({"detail": f"Интерфейс {interface_name} не найден!"})

    # Если в профиле пользователя стоит ограничение на определенные порты
    if profile.port_guard_pattern and re.search(
        profile.port_guard_pattern,
        interface.desc,
        flags=re.IGNORECASE,
    ):
        raise PermissionDenied(detail="Запрещено изменять состояние данного порта!")

    # Если недостаточно привилегий для изменения статуса порта
    if profile is not None and profile.perm_level < 2 and action in ["up", "down"]:
        # Логи
        log(
            user,
            device,
            f"Tried to set port {interface.name} ({interface.desc}) "
            f'to the "{action}" state, but was refused \n',
        )
        raise PermissionDenied(detail="У вас недостаточно прав, для изменения состояния порта!")

    return interface


def change_port_state(device: models.Devices, *, port_name: str, port_status: str, save_config: bool) -> str:
    """
    Изменяет состояние порта на оборудовании
    """
    # Если оборудование Недоступно
    if not device.available:
        raise APIException({"error": "Оборудование недоступно!"})

    session = device.connect()
    # Перезагрузка порта
    if port_status == "reload":
        port_change_status = session.reload_port(
            port=port_name,
            save_config=save_config,
        )

    # UP and DOWN
    else:
        port_change_status = session.set_port(
            port=port_name,
            status=port_status,
            save_config=save_config,
        )

    if "Неверный порт" in port_change_status:
        raise ValidationError({"error": "Неверный порт!"})

    return port_change_status


def set_interface_description(
    device: models.Devices, *, interface_name: str, description: str
) -> SetDescriptionResult:
    """Устанавливает описание интерфейса"""
    set_description_status = device.connect().set_description(port=interface_name, desc=description)

    if set_description_status.max_length:
        # Если есть данные, что описание слишком длинное.
        raise ValidationError(
            {
                "detail": "Слишком длинное описание! "
                f"Укажите не более {set_description_status.max_length} символов."
            }
        )

    if set_description_status.error:
        if set_description_status.error == "Неверный порт":
            raise ValidationError({"detail": f"Неверный порт {interface_name}"})
        else:
            raise APIException(detail=set_description_status.error)

    return set_description_status


def get_mac_addresses_on_interface(device: models.Devices, interface_name: str) -> list[dict]:
    """Возвращает MAC адреса, которые находятся на интерфейсе"""
    vlan_names = {str(v["vid"]): v["name"] for v in VlanName.objects.all().values("vid", "name")}

    macs = []  # Итоговый список
    for vid, mac in device.connect().get_mac(interface_name):  # Смотрим VLAN и MAC
        macs.append(
            {
                "vlanID": vid,
                "mac": mac,
                "vlanName": vlan_names.get(str(vid), ""),
            }
        )
    return macs


def get_interface_detail_info(device: models.Devices, interface_name: str) -> dict:
    """Возвращает подробную информацию об интерфейсе"""

    # Если оборудование недоступно
    if not device.available:
        raise APIException({"detail": "Оборудование недоступно!"})

    result: dict[str, Any] = {}
    session = device.connect()

    result["portDetailInfo"] = session.get_port_info(interface_name)
    result["portConfig"] = session.get_port_config(interface_name)
    result["portType"] = session.get_port_type(interface_name)
    result["portErrors"] = session.get_port_errors(interface_name)
    result["hasCableDiag"] = True

    _add_comments_to_onts_lines(result, interface_name, device)

    return result


def _add_comments_to_onts_lines(data: dict, gpon_port: str, device: models.Devices) -> dict:
    """
    Находит комментарии созданные на ONT для порта `gpon_port` оборудования `device`.

    :param data: Текущий список данных.
    :param gpon_port: Основной GPON порт.
    :param device: Оборудование, на котором надо искать комментарии.
    :return: Список данных ONT с добавлением в конец списка возможных комментариев.
    """

    # Ищем возможные комментарии только для GPON типа
    if not (data.get("portDetailInfo", {}).get("data") and "gpon" in data["portDetailInfo"].get("type", "")):
        return data  # Если не GPON, то ничего не делаем.

    onts_lines = data["portDetailInfo"]["data"].get("onts_lines", [])
    if not onts_lines:
        return data  # Если нет ONT, то ничего не делаем.

    # Смотрим комментарии на порту оборудования, который начинается на переданный gpon порт.
    interfaces_comments = (
        device.interfacescomments_set.select_related("user")
        .filter(interface__startswith=gpon_port)
        .values("comment", "interface", "id", "user__username", "datetime")
    )
    ont_interfaces_dict: dict[str, list] = {}

    for comment in interfaces_comments:
        comment_data = {
            "text": comment["comment"],
            "user": comment["user__username"],
            "id": comment["id"],
            "createdTime": comment["datetime"],
        }
        if ont_interfaces_dict.get(comment["interface"]):
            ont_interfaces_dict[comment["interface"]].append(comment_data)
        else:
            ont_interfaces_dict[comment["interface"]] = [comment_data]

    new_onts_lines = []

    for line in onts_lines:
        # Соединяем порт GPON и ONTid
        ont_full_port = f"{gpon_port}/{line[0]}"
        # Добавляем комментарии либо пустой список в конец
        new_onts_lines.append(line + [ont_interfaces_dict.get(ont_full_port, [])])

    data["portDetailInfo"]["data"]["onts_lines"] = new_onts_lines

    return data
