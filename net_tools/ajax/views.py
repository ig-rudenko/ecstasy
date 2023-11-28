from functools import reduce

import orjson
import requests as requests_lib
from django.contrib.auth.decorators import login_required, permission_required
from django.core.cache import cache
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from pyvis.network import Network
from requests import RequestException

from app_settings.models import VlanTracerouteConfig, ZabbixConfig
from check.models import Devices
from devicemanager.device import ZabbixAPIConnection
from ..arp_find import find_mac_or_ip
from ..finder import (
    Finder,
    VlanTraceroute,
    MultipleVlanTraceroute,
)
from ..models import VlanName
from ..network import VlanNetwork
from ..tasks import interfaces_scan, check_scanning_status


@login_required
@permission_required(perm="auth.access_run_interfaces_gather", raise_exception=True)
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

    resp = requests_lib.get("https://api.maclookup.app/v2/macs/" + mac, timeout=2)
    if resp.status_code == 200:
        data = resp.json()
        return JsonResponse(
            {
                "vendor": data["company"],
                "address": data["address"],
            }
        )
    return JsonResponse({"vendor": resp.status_code})


@login_required
@permission_required(perm="auth.access_desc_search", raise_exception=True)
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


@login_required
@permission_required(perm="auth.access_wtf_search", raise_exception=True)
def ip_mac_info(request, ip_or_mac: str):
    """
    Считывает из БД таблицу с оборудованием, на которых необходимо искать MAC через таблицу arp

    В многопоточном режиме собирает данные ip, mac, vlan, agent-remote-id, agent-circuit-id из оборудования
     и проверяет, есть ли в Zabbix узел сети с таким IP и добавляет имя и hostid
    """
    arp_info = find_mac_or_ip(ip_or_mac)

    zabbix_url = ZabbixConfig.load().url

    names = []  # Список имен оборудования и его hostid из Zabbix
    if len(arp_info) > 0:
        # Если получили совпадение
        # Поиск всех IP-адресов в списке совпадений.
        ips = reduce(
            lambda x, y: x + y, map(lambda r: [line.ip for line in r.results], arp_info)
        )

        try:
            with ZabbixAPIConnection().connect() as zbx:
                # Ищем хост по IP
                hosts = zbx.host.get(
                    output=["name", "status"],
                    filter={"ip": ips},
                    selectInterfaces=["ip"],
                )
            names = [[h["name"], h["hostid"]] for h in hosts if h["status"] == "0"]
        except RequestException:
            pass

    return render(
        request,
        "tools/mac_result_for_modal.html",
        {"info": arp_info, "zabbix": names, "zabbix_url": zabbix_url},
    )


@login_required
@permission_required(perm="auth.access_traceroute", raise_exception=True)
def get_vlan_desc(request) -> JsonResponse:
    """
    ## Возвращаем имя VLAN, который был передан в HTTP запросе
    """

    try:
        # Получение имени vlan из базы данных.
        vlan: VlanName = VlanName.objects.get(vid=int(request.GET.get("vlan", "")))
        # Возвращает ответ JSON с именем vlan.
        return JsonResponse({"name": vlan.name, "description": vlan.description})

    except (VlanName.DoesNotExist, ValueError):
        # Возврат пустого объекта JSON.
        return JsonResponse({"name": "", "description": ""})


@login_required
@permission_required(perm="auth.access_traceroute", raise_exception=True)
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

    empty_ports = request.GET.get("ep") == "true"
    only_admin_up = request.GET.get("ad") == "true"
    double_check = request.GET.get("double-check") == "true"
    try:
        graph_min_length = int(request.GET.get("graph-min-length", 0))
    except ValueError:
        graph_min_length = 0
    try:
        vlan = int(request.GET.get("vlan"))
    except ValueError:
        return JsonResponse({"detail": "VLAN должен быть числом"}, status=400)

    # Загрузка объекта VlanTracerouteConfig из базы данных.
    vlan_traceroute_settings = VlanTracerouteConfig.load()

    tracert = MultipleVlanTraceroute(
        finder=VlanTraceroute(), devices_queryset=Devices.objects.all()
    )
    result = tracert.execute_traceroute(
        vlan=vlan,
        empty_ports=empty_ports,
        double_check=double_check,
        only_admin_up=only_admin_up,
        graph_min_length=graph_min_length,
        find_device_pattern=vlan_traceroute_settings.find_device_pattern,
    )

    if not result:  # Если поиск не дал результатов
        return JsonResponse(
            {
                "nodes": [],
                "edges": [],
                "options": {},
            }
        )

    network = VlanNetwork(
        network=Network(
            height="100%", width="100%", bgcolor="#222222", font_color="white"
        )
    )

    network.create_network(result, show_admin_down_ports=only_admin_up)

    return JsonResponse(
        {
            "nodes": network.nodes,
            "edges": network.edges,
            "options": orjson.loads(network.options.to_json()),
        }
    )
