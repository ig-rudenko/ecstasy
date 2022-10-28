from re import findall, sub, IGNORECASE
from net_tools.models import DevicesInfo, DescNameFormat
import json


def find_description(finding_string: str, re_string: str) -> tuple:
    """ Поиск портов на всем оборудовании, описание которых совпадает с finding_string """

    result = []
    count = 0

    all_devices = DevicesInfo.objects.all()

    # Производим поочередный поиск
    for device in all_devices:
        try:
            interfaces = json.loads(device.interfaces)
            if not interfaces:
                continue
            for line in interfaces:
                if (finding_string and finding_string.lower() in line.get('Description').lower()) or \
                        (re_string and findall(re_string, line.get('Description'), flags=IGNORECASE)):
                    # Если нашли совпадение в строке

                    # Ищем искомый фрагмент
                    replaced_str = findall(finding_string or re_string, line['Description'], flags=IGNORECASE)[0]

                    result.append({
                        'Device': device.device_name or 'Dev' + ' ' + device.ip,
                        'Interface': line['Interface'],

                        # Выделяем искомый фрагмент с помощью тега <mark></mark>
                        'Description': sub(
                            replaced_str, f'<mark>{replaced_str}</mark>', line['Description'], flags=IGNORECASE
                        ),
                        'original_desc': line['Description'],
                        'SavedTime': device.interfaces_date.strftime('%d.%m.%Y %H:%M:%S'),
                        'percent': '100%'
                    })
                    count += 1

        except Exception as e:
            print(e)

    return result, count


def reformatting(name: str):
    """ Форматируем строку с названием оборудования, приводя его в единый стандарт, указанный в DescNameFormat """

    for reformat in list(DescNameFormat.objects.all()):
        if reformat.standard == name:  # Если имя совпадает с правильным, то отправляем его
            return name

        for pattern in reformat.replacement.split(', '):
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

    vlans = []
    for v_range in vlans_ranges:
        if len(v_range.split()) > 1:
            vlans += list(vlan_range(v_range.split()))
        try:
            if '-' in v_range:
                parts = v_range.split('-')
                vlans += range(int(parts[0]), int(parts[1]) + 1)
            else:
                vlans.append(int(v_range))
        except ValueError:
            pass

    return set(vlans)


def find_vlan(device: str, vlan_to_find: int, passed_devices: set, result: list, empty_ports: str,
              only_admin_up: str, find_device_pattern: str):
    """
    Осуществляет поиск VLAN'ов по портам оборудования

    :param device: Имя устройства, на котором осуществляется поиск
    :param vlan_to_find: VLAN, который ищем
    :param passed_devices:  Уже пройденные устройства
    :param result:  Итоговый список
    :param empty_ports:  Включать пустые порты в анализ? 'true', 'false'
    :param only_admin_up:  Включать порты со статусом admin down в анализ? 'true', 'false'
    :param find_device_pattern:  Регулярное выражение, которое позволит найди оборудование в описании порта
    """

    admin_status = ''  # Состояние порта

    passed_devices.add(device)  # Добавляем узел в список уже пройденных устройств
    try:
        dev = DevicesInfo.objects.get(device_name=device)
    except DevicesInfo.DoesNotExist:
        return

    interfaces = json.loads(dev.vlans or '[]')
    if not interfaces:
        return

    intf_found_count = 0  # Кол-во найденных интерфейсов на этом устройстве

    for line in interfaces:
        vlans_list = []  # Список VLAN'ов на порту

        # Если вланы сохранены в виде строки
        if isinstance(line["VLAN's"], str):
            if 'all' in line["VLAN's"] or line["VLAN's"].strip() == 'trunk':
                # Если разрешено пропускать все вланы
                vlans_list = list(range(1, 4097))  # 1-4096
            else:
                if 'to' in line["VLAN's"]:
                    # Если имеется формат "711 800 to 804 1959 1961 1994 2005"
                    # Определяем диапазон 800 to 804
                    vv = [list(range(int(v[0]), int(v[1]) + 1)) for v in findall(r'(\d+)\s*to\s*(\d+)', line["VLAN's"])]
                    for v in vv:
                        vlans_list += v
                    # Добавляем единичные 711 800 to 801 1959 1961 1994 2005

                    vlans_list += line["VLAN's"].split()
                else:
                    # Формат представления стандартный "trunk,123,33,10-100"
                    vlans_list = vlan_range(
                        [
                            v for v in line["VLAN's"].split(',')
                            if v != 'trunk' and v not in ('trunk', 'access', 'hybrid', 'dot1q-tunnel')
                        ]
                    )
                    # Если искомый vlan находится в списке vlan'ов на данном интерфейсе

        # Если вланы сохранены в виде списка числовых элементов
        elif isinstance(line["VLAN's"], list) and all(str(v).isdigit() for v in line["VLAN's"]):
            vlans_list = line["VLAN's"]

        # Если нашли влан в списке вланов
        if vlan_to_find in vlans_list or str(vlan_to_find) in vlans_list:

            intf_found_count += 1

            next_device = findall(find_device_pattern, line["Description"])  # Ищем в описании порта следующий узел сети
            # Приводим к единому формату имя узла сети
            next_device = reformatting(next_device[0]) if next_device else ''

            # Пропускаем порты admin down, если включена опция only admin up
            if only_admin_up == 'true':
                admin_status = 'down' if \
                    'down' in str(line.get('Admin Status')).lower() or 'dis' in str(line.get('Admin Status')).lower() \
                    or 'admin down' in str(line.get('Status')).lower() or 'dis' in str(line.get('Status')).lower() \
                    else 'up'

            # Создаем данные для visual map
            if next_device:
                # Следующий узел сети
                result.append(
                    (
                        device,  # Устройство (название узла)
                        next_device,  # Сосед (название узла)
                        10,  # Толщина линии соединения
                        f'{device} ({line["Interface"]}) --- {line["Description"]}',  # Описание линии соединения
                        admin_status
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
                        admin_status
                    )
                )
            # Пустые порты
            elif empty_ports == 'true':
                result.append(
                    (
                        device,  # Устройство (название узла)
                        f'{device} p:({line["Interface"]})',  # Порт (название узла)
                        5,  # Толщина линии соединения
                        line["Interface"],  # Описание линии соединения
                        admin_status
                    )
                )

            if next_device and next_device not in list(passed_devices):
                find_vlan(
                    next_device,
                    vlan_to_find,
                    passed_devices,
                    result=result,
                    empty_ports=empty_ports,
                    only_admin_up=only_admin_up,
                    find_device_pattern=find_device_pattern
                )
