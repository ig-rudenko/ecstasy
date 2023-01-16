from re import findall, sub, IGNORECASE, match
from django.contrib.auth.models import User

from .models import DevicesInfo, DescNameFormat
from check.models import Devices
import json


def find_description(pattern: str, user: User) -> list:
    """
    # Поиск портов на всем оборудовании, описание которых совпадает с finding_string или re_string

    Возвращаем кортеж из списка результатов поиска и количество найденных описаний

    Список результатов содержит следующие элементы:

    ```python
    {
        "Device": "Имя оборудования",
        "Interface": "Порт",
        "Description": "Описание",
        "SavedTime": "Дата и время" # В формате "%d.%m.%Y %H:%M:%S",
    }
    ```

    :param pattern: Регулярное выражение, по которому будет осуществляться поиск описания портов.
    :param user: Поль
    :return: Список результатов поиска
    """

    result = []

    user_groups = [g["id"] for g in user.profile.devices_groups.all().values("id")]

    # Производим поочередный поиск
    for device in DevicesInfo.objects.all():
        try:
            if Devices.objects.get(ip=device.ip).group_id not in user_groups:
                continue
        except Devices.DoesNotExist:
            continue

        # Загрузка данных json из базы данных в словарь python.
        interfaces = json.loads(device.interfaces)
        # Проверяем, пуста ли переменная interfaces.
        if not interfaces:
            continue
        for line in interfaces:

            if not line.get("Description"):
                continue
            # Он проверяет, находится ли pattern в описании.

            if match(pattern, line.get("Description"), flags=IGNORECASE):
                # Если нашли совпадение в строке

                result.append(
                    {
                        "Device": device.device_name or "Dev" + " " + device.ip,
                        "Interface": line["Interface"],
                        "Description": line["Description"],
                        "SavedTime": device.interfaces_date.strftime(
                            "%d.%m.%Y %H:%M:%S"
                        ),
                    }
                )

    return result


def reformatting(name: str):
    """Форматируем строку с названием оборудования, приводя его в единый стандарт, указанный в DescNameFormat"""

    for reformat in list(DescNameFormat.objects.all()):
        if reformat.standard == name:
            # Если имя совпадает с правильным, то отправляем его
            return name

        for pattern in reformat.replacement.split(", "):
            if pattern in name:  # Если паттерн содержится в исходном имени

                # Заменяем совпадение "pattern" в названии "name" на правильное "n"
                return sub(pattern, reformat.standard, name)

    # Если не требуется замены
    return name


def vlan_range(vlans_ranges: list) -> set:
    """
    Преобразовывает сокращенные диапазоны VLAN'ов в развернутый список

    14, 100-103, 142 -> 14, 100, 101, 102, 103, 142

    :param vlans_ranges: Список диапазонов
    :return: развернутое множество VLAN'ов
    """

    vlans = set()
    for v_range in vlans_ranges:
        for r in v_range.split():
            if "-" in r:
                start, end = map(int, findall(r"\d+", r))
                vlans.update(range(start, end + 1))
            else:
                vlans.add(int(r))
    return vlans


def find_vlan(
    device: str,
    vlan_to_find: int,
    passed_devices: set,
    result: list,
    empty_ports: str,
    only_admin_up: str,
    find_device_pattern: str,
):
    """
    ## Осуществляет поиск VLAN'ов по портам оборудования.

    Функция загружает данные об устройстве из базы данных, парсит информацию о VLAN на портах,
    и если находит совпадение с искомым VLAN, то добавляет информацию в итоговый список.

    :param device: Имя устройства, на котором осуществляется поиск
    :param vlan_to_find: VLAN, который ищем
    :param passed_devices:  Уже пройденные устройства
    :param result:  Итоговый список
    :param empty_ports:  Включать пустые порты в анализ? ('true', 'false')
    :param only_admin_up:  Включать порты со статусом admin down в анализ? ('true', 'false')
    :param find_device_pattern:  Регулярное выражение, которое позволит найти оборудование в описании порта
    """

    admin_status = ""  # Состояние порта

    passed_devices.add(device)  # Добавляем узел в список уже пройденных устройств
    try:
        dev = DevicesInfo.objects.get(device_name=device)
    except DevicesInfo.DoesNotExist:
        return

    interfaces = json.loads(dev.vlans or "[]")
    if not interfaces:
        return

    intf_found_count = 0  # Кол-во найденных интерфейсов на этом устройстве

    for line in interfaces:
        vlans_list = []  # Список VLAN'ов на порту

        # Если вланы сохранены в виде строки
        if isinstance(line["VLAN's"], str):
            if "all" in line["VLAN's"] or line["VLAN's"].strip() == "trunk":
                # Если разрешено пропускать все вланы
                vlans_list = list(range(1, 4097))  # 1-4096
            else:
                if "to" in line["VLAN's"]:
                    # Если имеется формат "711 800 to 804 1959 1961 1994 2005"
                    # Определяем диапазон 800 to 804
                    vv = [
                        list(range(int(v[0]), int(v[1]) + 1))
                        for v in findall(r"(\d+)\s*to\s*(\d+)", line["VLAN's"])
                    ]
                    for v in vv:
                        vlans_list += v
                    # Добавляем единичные 711 800 to 801 1959 1961 1994 2005

                    vlans_list += line["VLAN's"].split()
                else:
                    # Формат представления стандартный "trunk,123,33,10-100"
                    vlans_list = vlan_range(
                        [
                            v
                            for v in line["VLAN's"].split(",")
                            if v != "trunk"
                            and v not in ("trunk", "access", "hybrid", "dot1q-tunnel")
                        ]
                    )
                    # Если искомый vlan находится в списке vlan'ов на данном интерфейсе

        # Если вланы сохранены в виде списка числовых элементов
        elif isinstance(line["VLAN's"], list) and all(
            str(v).isdigit() for v in line["VLAN's"]
        ):
            vlans_list = line["VLAN's"]

        # Если нашли влан в списке вланов
        if vlan_to_find in vlans_list or str(vlan_to_find) in vlans_list:

            intf_found_count += 1

            # Ищем в описании порта следующий узел сети
            next_device = findall(find_device_pattern, line["Description"])
            # Приводим к единому формату имя узла сети
            next_device = reformatting(next_device[0]) if next_device else ""

            # Пропускаем порты admin down, если включена опция only admin up
            if only_admin_up == "true":
                admin_status = (
                    "down"
                    if "down" in str(line.get("Admin Status")).lower()
                    or "dis" in str(line.get("Admin Status")).lower()
                    or "admin down" in str(line.get("Status")).lower()
                    or "dis" in str(line.get("Status")).lower()
                    else "up"
                )

            # Создаем данные для visual map
            if next_device:
                # Следующий узел сети
                result.append(
                    (
                        device,  # Устройство (название узла)
                        next_device,  # Сосед (название узла)
                        10,  # Толщина линии соединения
                        f'{device} ({line["Interface"]}) --- {line["Description"]}',  # Описание линии соединения
                        admin_status,
                    )
                )
            # Порт с описанием
            elif line["Description"]:
                result.append(
                    (
                        device,  # Устройство (название узла)
                        f'{device} d:({line["Description"]})',  # Порт (название узла)
                        10,  # Толщина линии соединения
                        line["Interface"],  # Описание линии соединения
                        admin_status,
                    )
                )
            # Пустые порты
            elif empty_ports == "true":
                result.append(
                    (
                        device,  # Устройство (название узла)
                        f'{device} p:({line["Interface"]})',  # Порт (название узла)
                        5,  # Толщина линии соединения
                        line["Interface"],  # Описание линии соединения
                        admin_status,
                    )
                )

            # Проверка наличия следующего устройства в списке пройденных устройств.
            if next_device and next_device not in list(passed_devices):
                find_vlan(
                    next_device,
                    vlan_to_find,
                    passed_devices,
                    result=result,
                    empty_ports=empty_ports,
                    only_admin_up=only_admin_up,
                    find_device_pattern=find_device_pattern,
                )
