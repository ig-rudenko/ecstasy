from typing import List

import orjson
from re import findall
from concurrent.futures import ThreadPoolExecutor

import requests as requests_lib
from requests import RequestException
from pyvis.network import Network

from django.core.cache import cache
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required

from app_settings.models import VlanTracerouteConfig
from check.models import Devices
from devicemanager import ZabbixAPIConnection
from ..finder import Finder, VlanTraceroute, VlanTracerouteResult
from ..models import VlanName, DevicesForMacSearch
from ..tasks import interfaces_scan, check_scanning_status


@login_required
def run_periodically_scan(request):
    if request.method == "POST":
        task_id = cache.get("periodically_scan_id")
        if not task_id:
            task_id = interfaces_scan.delay()
            cache.set("periodically_scan_id", task_id, timeout=None)
            return HttpResponse(status=200)

    return HttpResponse(status=400)


@login_required
def check_periodically_scan(request):
    return JsonResponse(check_scanning_status())


@login_required
def get_vendor(request, mac: str) -> JsonResponse:
    """Определяет производителя по MAC адресу"""

    resp = requests_lib.get("https://macvendors.com/query/" + mac, timeout=2)
    if resp.status_code == 200:
        return JsonResponse({"vendor": resp.text})
    return JsonResponse({"vendor": ""})


@login_required
def find_as_str(request):
    """
    ## Вывод результата поиска портов по описанию
    """

    if not request.GET.get("pattern"):
        return JsonResponse({"interfaces": []})

    result = Finder.find_description(request.GET.get("pattern"), request.user)

    return JsonResponse(
        {"interfaces": result},
    )


def get_ip_or_mac_from(model_dev, find_address: str, result: list, find_type: str) -> None:
    """
    ## Подключается к оборудованию, смотрит MAC адрес в таблице arp и записывает результат в список result

    :param model_dev: Оборудование, на котором надо искать
    :param find_address: Адрес который надо искать (IP или MAC)
    :param result: Список в который будет добавлен результат
    :param find_type: Тип поиска ```"IP"``` или ```"MAC"```
    """

    with model_dev.connect() as session:
        info = []
        # Проверка, является ли find_type IP-адресом и имеет ли сеанс атрибут search_ip.
        if find_type == "IP" and hasattr(session, "search_ip"):
            info: list = session.search_ip(find_address)

        # Проверка того, является ли find_type MAC-адресом и имеет ли сеанс атрибут search_mac.
        elif find_type == "MAC" and hasattr(session, "search_mac"):
            info: list = session.search_mac(find_address)

        if info:
            info.append(model_dev.name)  # Добавляем имя оборудования к результату
            result.append(info)


@login_required
def ip_mac_info(request, ip_or_mac):
    """
    Считывает из БД таблицу с оборудованием, на которых необходимо искать MAC через таблицу arp

    В многопоточном режиме собирает данные ip, mac, vlan, agent-remote-id, agent-circuit-id из оборудования
     и проверяет, есть ли в Zabbix узел сети с таким IP и добавляет имя и hostid
    """

    # Получение устройств из базы данных, которые используются в поиске MAC/IP адресов
    devices_for_search = DevicesForMacSearch.objects.all()

    # Поиск IP-адреса в строке.
    find_address = findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", ip_or_mac)
    if find_address:
        # Нашли IP адрес
        find_type: str = "IP"
        find_address = find_address[0]

    else:
        # Поиск всех шестнадцатеричных символов из входной строки.
        find_address = "".join(findall(r"[a-fA-F\d]", ip_or_mac)).lower()
        # Нашли MAC адрес
        find_type: str = "MAC"
        # Проверка правильности MAC-адреса.
        if not find_address or len(find_address) < 6 or len(find_address) > 12:
            return []

    match = []
    # Менеджер контекста, который создает пул потоков и выполняет код внутри блока with.
    with ThreadPoolExecutor() as execute:
        # Проходит через каждое устройство в списке устройств.
        for dev in devices_for_search:
            # Отправка задачи в пул потоков.
            execute.submit(get_ip_or_mac_from, dev.device, find_address, match, find_type)

    names = []  # Список имен оборудования и его hostid из Zabbix

    if len(match) > 0:
        # Если получили совпадение
        # Поиск всех IP-адресов в списке совпадений.
        ip = findall(r"\d+\.\d+\.\d+\.\d+", str(match))

        try:
            with ZabbixAPIConnection().connect() as zbx:
                # Ищем хост по IP
                hosts = zbx.host.get(
                    output=["name", "status"],
                    filter={"ip": ip},
                    selectInterfaces=["ip"],
                )
            names = [[h["name"], h["hostid"]] for h in hosts if h["status"] == "0"]
        except RequestException:
            pass

    return render(request, "tools/mac_result_for_modal.html", {"info": match, "zabbix": names})


@login_required
def get_vlan_desc(request) -> JsonResponse:
    """
    ## Возвращаем имя VLAN, который был передан в HTTP запросе
    """

    try:
        # Получение vlan из запроса.
        vlan = int(request.GET.get("vlan"))
        # Получение имени vlan из базы данных.
        vlan_name = VlanName.objects.get(vid=vlan).name
        # Возвращает ответ JSON с именем vlan.
        return JsonResponse({"vlan_desc": vlan_name})

    except (VlanName.DoesNotExist, ValueError):
        # Возврат пустого объекта JSON.
        return JsonResponse({})


def create_nodes(result: List[VlanTracerouteResult], net: Network, show_admin_down_ports: bool):
    """
    ## Создает элементы и связи между ними для карты VLAN
    """

    for e in result:
        # По умолчанию зеленый цвет, форма точки
        src_gr = 3
        dst_gr = 3
        src_shape = "dot"
        dst_shape = "dot"
        src_label = e.node
        dst_label = e.next_node
        line_width = e.line_width

        # ASW: желтый
        if "ASW" in e.node:
            src_gr = 1
        if "ASW" in e.next_node:
            dst_gr = 1

        # SSW: голубой
        if "SSW" in e.node:
            src_gr = 0
        if "SSW" in e.next_node:
            dst_gr = 0

        # Порт: зеленый, форма треугольника - △
        if "-->" in e.node.lower():
            src_gr = 3
            src_shape = "triangle"
            src_label = e.node.split("-->")[1]
        if "-->" in e.next_node.lower():
            dst_gr = 3
            dst_shape = "triangle"
            dst_label = e.node.split("-->")[1]

        # DSL: оранжевый, форма квадрата - ☐
        if "DSL" in e.node:
            src_gr = 6
            src_shape = "square"
        if "DSL" in e.next_node:
            dst_gr = 6
            dst_shape = "square"

        # CORE: розовый, форма ромба - ◊
        if "SVSL-99-GP15-SSW" in e.node or "SVSL-99-GP15-SSW" in e.next_node:
            src_gr = 4
            src_shape = "diamond"
        if "core" in e.node.lower() or "-cr" in e.next_node.lower():
            src_gr = 4
            src_shape = "diamond"
        if "core" in e.next_node.lower() or "-cr" in e.node.lower():
            dst_gr = 4
            dst_shape = "diamond"

        # Пустой порт: светло-зеленый, форма треугольника - △
        if "p:(" in e.node.lower():
            src_gr = 9
            src_shape = "triangle"
            src_label = e.node.split("p:(")[1][:-1]
        if "p:(" in e.next_node.lower():
            dst_gr = 9
            dst_shape = "triangle"
            dst_label = e.next_node.split("p:(")[1][:-1]

        # Только описание: зеленый
        if "d:(" in e.node.lower():
            src_gr = 3
            src_label = e.node.split("d:(")[1][:-1]
        if "d:(" in e.next_node.lower():
            dst_gr = 3
            dst_label = e.next_node.split("d:(")[1][:-1]

        # Если стиль отображения admin down status
        if show_admin_down_ports and e.admin_down_status == "down":
            line_width = 0.5  # ширина линии связи
        # print(src, admin_status)

        all_nodes = net.get_nodes()
        # Создаем узлы, если их не было
        if e.node not in all_nodes:
            net.add_node(e.node, src_label, title=src_label, group=src_gr, shape=src_shape)

        if e.next_node not in all_nodes:
            net.add_node(e.next_node, dst_label, title=dst_label, group=dst_gr, shape=dst_shape)

        # Добавление ребра между двумя узлами.
        net.add_edge(e.node, e.next_node, value=line_width, title=e.line_description)


def add_node_neighbors(node, neighbor_list: List[str]):
    title = node["title"] + " Соединено:"

    for i, dev in enumerate(neighbor_list, 1):
        title += f"""<br>{i}. <span>{dev}</span>"""

    node["title"] = title


@login_required
def get_vlan(request):
    """
    ## Трассировка VLAN и отправка карты

    Эта функция обрабатывает GET-запрос для трассировки VLAN.
    Она использует декоратор @login_required для проверки авторизации пользователя.
    Если в запросе не содержится параметр vlan, функция возвращает пустой JSON объект.
    Затем, используя метод load() класса VlanTracerouteConfig, загружает настройки трассировки VLAN из базы данных.

    Функция также идентифицирует список устройств, откуда будет начинаться трассировка VLAN,
    и определяет паттерн для поиска интерфейсов.
    Далее функция использует цикл for для перебора списка устройств, используемых для запуска трассировки VLAN.
    Для каждого устройства функция вызывает функцию find_vlan(), которая ищет VLAN с помощью рекурсивного алгоритма
    и возвращает список узлов сети, соседей и линий связи для визуализации.
    Если функция find_vlan() вращает результат, то цикл завершается.

    Если же результат не был найден ни для одного устройства из списка, функция возвращает HttpResponse "empty".
    Если результат был найден, функция создаёт экземпляр класса Network и добавляет к нему узлы сети,
    соседей и линии связи из результата. Затем функция отправляет карту в виде JSON-объекта как ответ на запрос.
    """

    # Если в запросе нет vlan, вернет пустой объект JSON.
    if not request.GET.get("vlan"):
        return JsonResponse({"data": {}})

    # Загрузка объекта VlanTracerouteConfig из базы данных.
    vlan_traceroute_settings = VlanTracerouteConfig.load()

    # Определяем список устройств откуда будет начинаться трассировка vlan
    vlan_start = vlan_traceroute_settings.vlan_start.split(", ")

    # Определяем паттерн для поиска интерфейсов
    if not vlan_traceroute_settings.find_device_pattern:
        # Если не нашли, то обнуляем список начальных устройств для поиска, чтобы не запускать трассировку vlan
        vlan_start = []

    finder = VlanTraceroute()

    # Цикл for, перебирающий список устройств, используемых для запуска трассировки VLAN.
    for start_dev in Devices.objects.all():
        start_dev: Devices
        try:
            # Преобразуем VLAN в число
            vlan = int(request.GET["vlan"])
        except ValueError:
            break
        # Трассировка vlan
        finder.find_vlan(
            device=start_dev.name,
            vlan_to_find=vlan,
            empty_ports=request.GET.get("ep") == "true",
            only_admin_up=request.GET.get("ad") == "true",
            find_device_pattern=vlan_traceroute_settings.find_device_pattern,
            double_check=request.GET.get("double-check") == "true",
        )

    result = finder.result

    if not result:  # Если поиск не дал результатов
        return HttpResponse("empty")

    net = Network(height="100%", width="100%", bgcolor="#222222", font_color="white")

    # Создаем невидимые элементы, для инициализации групп 0-9
    # 0 - голубой;      1 - желтый;     2 - красный;    3 - зеленый;            4 - розовый;
    # 5 - пурпурный;    6 - оранжевый;  7 - синий;      8 - светло-красный;     9 - светло-зеленый
    for i in range(10):
        net.add_node(i, i, title="", group=i, hidden=True)

    # Создаем элементы и связи между ними
    create_nodes(result, net, request.GET.get("ad") == "true")

    neighbor_map = net.get_adj_list()
    nodes_count = len(net.nodes)

    # Настройка физики для карты сети.
    net.repulsion(node_distance=nodes_count if nodes_count > 130 else 130, damping=0.89)

    # Итерация по всем узлам в сети.
    for node in net.nodes:
        # Установка размера узла на основе количества соседей.
        node["value"] = len(neighbor_map[node["id"]]) * 3
        if "core" in node["title"].lower():
            node["value"] = 70
        if "-cr" in node["title"].lower():
            node["value"] = 100
        # Пустой порт.
        # Устанавливаем размер узла равным 1, если узел является портом.
        if "p:(" in node["title"]:
            node["value"] = 1
        # Добавление списка соседей в заголовок узла.
        add_node_neighbors(node, neighbor_map[node["id"]])

    # Установка сглаживания краев на динамическое.
    net.set_edge_smooth("dynamic")

    return JsonResponse(
        {
            "nodes": net.nodes,
            "edges": net.edges,
            "options": orjson.loads(net.options.to_json()),
        }
    )
