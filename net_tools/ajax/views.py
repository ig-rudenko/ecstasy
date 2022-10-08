import os
from re import findall
import requests as requests_lib
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required

from net_tools.finder import find_description, find_vlan
from net_tools.models import VlanName, DevicesForMacSearch
from devicemanager.device import Device

from app_settings.models import ZabbixConfig, VlanTracerouteConfig
from ecstasy_project.settings import BASE_DIR
from pyzabbix import ZabbixAPI
from pyvis.network import Network

from concurrent.futures import ThreadPoolExecutor


@login_required
def get_vendor(request, mac):
    """ Определяет производителя по MAC адресу """

    resp = requests_lib.get('https://macvendors.com/query/'+mac)
    if resp.status_code == 200:
        return JsonResponse({'vendor': resp.text})
    return JsonResponse({'vendor': ''})


@login_required
def find_as_str(request):
    """ Вывод результата поиска портов по описанию """

    if not request.GET.get('string'):
        return JsonResponse({
            'data': []
        })
    result, count = find_description(
        finding_string=request.GET.get('string') if request.GET.get('type') == 'string' else '',
        re_string=request.GET.get('string') if request.GET.get('type') == 'regex' else ''
    )

    return render(
        request, 'tools/descriptions_table.html',
        {
            'data': result,
            'count': count,
            'pattern': request.GET.get('string')
        }
    )


def get_mac_from(model_dev, mac_address: str, result: list):
    """ Подключается к оборудованию, смотрит MAC адрес в таблице arp и записывает результат в список result """

    dev = Device(model_dev.name)
    with dev.connect(protocol=model_dev.cmd_protocol, auth_obj=model_dev.auth_group) as session:
        if hasattr(session, 'search_mac'):
            res = session.search_mac(mac_address)
            if res:
                result.append([', '.join(res[0])])


@login_required
def mac_info(request, mac):
    """
    Считывает из БД таблицу с оборудованием, на которых необходимо искать MAC через таблицу arp

    В многопоточном режиме собирает данные [ip, mac, vlan] из оборудования и проверяет,
    есть ли в Zabbix узел сети с таким IP и добавляет имя и hostid
    """

    devices_for_search = DevicesForMacSearch.objects.all()

    mac_address = ''.join(findall(r'[a-zA-Z\d]', mac)).lower()
    if not mac_address or len(mac_address) < 6 or len(mac_address) > 12:
        return []
    match = []
    with ThreadPoolExecutor() as execute:
        for dev in devices_for_search:
            execute.submit(get_mac_from, dev.device, mac, match)

    names = []  # Список имен оборудования и его hostid из Zabbix

    if len(match) > 0:
        # Если получили совпадение
        ip = findall(r'\d+\.\d+\.\d+\.\d+', str(match))

        zabbix_settings = ZabbixConfig.load()
        zbx = ZabbixAPI(server=zabbix_settings.url)
        zbx.login(user=zabbix_settings.login, password=zabbix_settings.password)
        # Ищем хост по IP
        hosts = zbx.host.get(output=['name', 'status'], filter={'ip': ip}, selectInterfaces=['ip'])
        names = [[h['name'], h['hostid']] for h in hosts if h['status'] == '0']

    return JsonResponse({
        'info': match,
        'zabbix': names
    })


@login_required
def get_vlan_desc(request):
    """ Получаем имя VLAN """

    try:
        vlan = int(request.GET.get('vlan'))
        vlan_name = VlanName.objects.get(vid=vlan).name

    except (VlanName.DoesNotExist, ValueError):
        return JsonResponse({})

    else:
        return JsonResponse({'vlan_desc': vlan_name})


@login_required
def get_vlan(request):
    """ Трассировка VLAN """

    if not request.GET.get('vlan'):
        return JsonResponse({
            'data': {}
        })

    vlan_traceroute_settings = VlanTracerouteConfig.load()

    # Определяем список устройств откуда будет начинаться трассировка vlan
    vlan_start = vlan_traceroute_settings.vlan_start.split(', ')

    # Определяем паттерн для поиска интерфейсов
    if not vlan_traceroute_settings.find_device_pattern:
        # Если не нашли, то обнуляем список начальных устройств для поиска, чтобы не запускать трассировку vlan
        vlan_start = []

    for start_dev in vlan_start:
        passed = set()  # Имена уже проверенных устройств
        result = []  # Список узлов сети, соседей и линий связи для визуализации

        try:
            vlan = int(request.GET['vlan'])
        except ValueError:
            break

        # трассировка vlan
        find_vlan(
            device=start_dev,
            vlan_to_find=vlan,
            passed_devices=passed,
            result=result,
            empty_ports=request.GET.get('ep'),
            only_admin_up=request.GET.get('ad'),
            find_device_pattern=vlan_traceroute_settings.find_device_pattern
        )
        if result:  # Если поиск дал результат, то прекращаем
            break

    else:  # Если поиск не дал результатов
        return HttpResponse('empty')

    net = Network(height="100%", width="100%", bgcolor="#222222", font_color="white")

    # Создаем невидимые элементы, для инициализации групп 0-9
    # 0 - голубой;  1 - желтый;  2 - красный;  3 - зеленый;  4 - розовый;
    # 5 - пурпурный;  6 - оранжевый;  7 - синий;  8 - светло-красный;  9 - светло-зеленый
    for i in range(10):
        net.add_node(i, i, title='', group=i, hidden=True)

    # Создаем элементы и связи между ними
    for e in result:
        src = e[0]
        dst = e[1]
        w = e[2]
        desc = e[3]
        admin_status = e[4]

        # По умолчанию зеленый цвет, форма точки
        src_gr = 3
        dst_gr = 3
        src_shape = 'dot'
        dst_shape = 'dot'
        src_label = src
        dst_label = dst

        # ASW: желтый
        if "ASW" in str(src):
            src_gr = 1
        if "ASW" in str(dst):
            dst_gr = 1

        # SSW: голубой
        if "SSW" in str(src):
            src_gr = 0
        if "SSW" in str(dst):
            dst_gr = 0

        # Порт: зеленый, форма треугольника - △
        if "-->" in str(src).lower():
            src_gr = 3
            src_shape = 'triangle'
            src_label = src.split('-->')[1]
        if "-->" in str(dst).lower():
            dst_gr = 3
            dst_shape = 'triangle'
            dst_label = src.split('-->')[1]

        # DSL: оранжевый, форма квадрата - ☐
        if "DSL" in str(src):
            src_gr = 6
            src_shape = 'square'
        if "DSL" in str(dst):
            dst_gr = 6
            dst_shape = 'square'

        # CORE: розовый, форма ромба - ◊
        if "SVSL-99-GP15-SSW" in src or "SVSL-99-GP15-SSW" in dst:
            src_gr = 4
            src_shape = 'diamond'
        if "core" in str(src).lower() or "-cr" in str(dst).lower():
            src_gr = 4
            src_shape = 'diamond'
        if "core" in str(dst).lower() or "-cr" in str(src).lower():
            dst_gr = 4
            dst_shape = 'diamond'

        # Пустой порт: светло-зеленый, форма треугольника - △
        if "p:(" in str(src).lower():
            src_gr = 9
            src_shape = 'triangle'
            src_label = src.split('p:(')[1][:-1]
        if "p:(" in str(dst).lower():
            dst_gr = 9
            dst_shape = 'triangle'
            dst_label = dst.split('p:(')[1][:-1]

        # Только описание: зеленый
        if "d:(" in str(src).lower():
            src_gr = 3
            src_label = src.split('d:(')[1][:-1]
        if "d:(" in str(dst).lower():
            dst_gr = 3
            dst_label = dst.split('d:(')[1][:-1]

        # Если стиль отображения admin down status
        if request.GET.get('ad') == 'true' and admin_status == 'down':
            w = 0.5  # ширина линии связи
        # print(src, admin_status)

        all_nodes = net.get_nodes()
        # Создаем узлы, если их не было
        if src not in all_nodes:
            net.add_node(src, src_label, title=src_label, group=src_gr, shape=src_shape)

        if dst not in all_nodes:
            net.add_node(dst, dst_label, title=src_label, group=dst_gr, shape=dst_shape)

        net.add_edge(src, dst, value=w, title=desc)

    neighbor_map = net.get_adj_list()
    nodes_count = len(net.nodes)

    print('Всего узлов создано:', nodes_count)
    # add neighbor data to node hover data

    # set the physics layout of the network
    net.repulsion(
        node_distance=nodes_count if nodes_count > 130 else 130,
        damping=0.89
    )

    for node in net.nodes:
        node["value"] = len(neighbor_map[node["id"]]) * 3
        if "core" in node["title"].lower():
            node["value"] = 70
        if "-cr" in node["title"].lower():
            node["value"] = 100
        # Пустой порт
        if "p:(" in node["title"]:
            node["value"] = 1
        node["title"] += " Соединено:<br>" + "<br>".join(neighbor_map[node["id"]])

    # net.show_buttons(filter_=True)
    net.set_edge_smooth('dynamic')

    if not os.path.exists(BASE_DIR / 'templates' / 'tools' / 'vlans'):
        os.makedirs(BASE_DIR / 'templates' / 'tools' / 'vlans')
    net.save_graph(f"templates/tools/vlans/vlan{request.GET['vlan']}.html")

    return render(request, f"tools/vlans/vlan{request.GET['vlan']}.html")
