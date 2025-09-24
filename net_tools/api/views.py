import re
from functools import reduce

import orjson
import requests as requests_lib
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.cache import cache
from django.http import HttpResponse
from pyvis.network import Network
from requests import RequestException
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from app_settings.models import VlanTracerouteConfig, ZabbixConfig
from check.models import Devices
from check.services.filters import filter_devices_qs_by_user
from devicemanager.device import zabbix_api
from net_tools.models import VlanName
from net_tools.services.arp_find import find_mac_or_ip
from net_tools.services.finder import Finder, MultipleVlanTraceroute, VlanTraceroute
from net_tools.services.network import VlanNetwork
from net_tools.tasks import check_scanning_status, interfaces_scan

from .serializers import GetVlanDescQuerySerializer, VlanTracerouteQuerySerializer
from .swagger.schemas import (
    find_by_description_schema,
    get_vendor_schema,
    get_vlan_desc_schema,
    vlan_traceroute_schema,
)


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


@api_view(["GET"])
@login_required
def check_periodically_scan(request: Request):
    return Response(check_scanning_status())


@get_vendor_schema
@api_view(["GET"])
@login_required
def get_vendor(request: Request, mac: str) -> Response:
    """Определяет производителя по MAC адресу"""
    proxies = {}
    if settings.PROXY_URL:
        proxies = {"http": settings.PROXY_URL, "https": settings.PROXY_URL}
    try:
        resp = requests_lib.get("https://api.maclookup.app/v2/macs/" + mac, timeout=2, proxies=proxies)
    except requests_lib.RequestException:
        return Response({"vendor": "Got exception!"})

    if resp.status_code == 200:
        data = resp.json()
        return Response(
            {
                "vendor": data["company"],
                "address": data["address"],
            }
        )
    return Response({"vendor": resp.status_code})


@find_by_description_schema
@api_view(["GET"])
@login_required
@permission_required(perm="auth.access_desc_search", raise_exception=True)
def find_by_description(request):
    """
    ## Поиск портов по описанию и комментариям.
    """

    is_regex = request.GET.get("is_regex", "0").lower() in ("1", "true")
    pattern = request.GET.get("pattern", "")
    if not pattern:
        return Response({"interfaces": []})

    if is_regex:
        try:
            re.compile(pattern)
        except re.PatternError as exc:
            return Response(data={"error": f"Ошибка в регулярном выражении: {exc}"}, status=400)

    devices_qs = filter_devices_qs_by_user(Devices.objects.all(), request.user)
    finder = Finder(devices_qs)
    result = finder.find_description(pattern_str=pattern, is_regex=is_regex)

    return Response({"interfaces": result})


@api_view(["GET"])
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
        ips = reduce(lambda x, y: x + y, map(lambda r: [line.ip for line in r.results], arp_info))

        try:
            with zabbix_api.connect() as zbx:
                # Ищем хост по IP
                hosts = zbx.host.get(
                    output=["name", "status"],
                    filter={"ip": ips},
                    selectInterfaces=["ip"],
                )
            names = [{"name": h["name"], "hostid": h["hostid"]} for h in hosts if h["status"] == "0"]
        except RequestException:
            pass

    arp_info_json = [
        {
            "device": {
                "name": info.device.name,
                "ip": info.device.ip,
            },
            "results": [
                {
                    "mac": res.mac,
                    "ip": res.ip,
                    "vlan": res.vlan,
                    "device_name": res.device_name,
                    "port": res.port,
                }
                for res in info.results
            ],
        }
        for info in arp_info
    ]

    return Response({"info": arp_info_json, "zabbix": names, "zabbix_url": zabbix_url})


@get_vlan_desc_schema
@api_view(["GET"])
@login_required
@permission_required(perm="auth.access_traceroute", raise_exception=True)
def get_vlan_desc(request: Request) -> Response:
    """
    ## Возвращаем имя VLAN, который был передан в HTTP запросе
    """
    serializer = GetVlanDescQuerySerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)

    data = {"name": "", "description": ""}

    try:
        # Получение имени vlan из базы данных.
        vlan: VlanName = VlanName.objects.get(vid=serializer.validated_data["vlan"])
    except VlanName.DoesNotExist:
        pass
    else:
        data = {"name": vlan.name or "", "description": vlan.description}

    # Возвращает ответ JSON с именем vlan.
    return Response(data)


@vlan_traceroute_schema
@api_view(["GET"])
@login_required
@permission_required(perm="auth.access_traceroute", raise_exception=True)
def get_vlan_traceroute(request: Request) -> Response:
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

    serializer = VlanTracerouteQuerySerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)

    vlan = serializer.validated_data["vlan"]
    empty_ports = serializer.validated_data["ep"]
    only_admin_up = serializer.validated_data["ad"]
    double_check = serializer.validated_data["double_check"]
    graph_min_length = serializer.validated_data["graph_min_length"]

    # Загрузка объекта VlanTracerouteConfig из базы данных.
    vlan_traceroute_settings = VlanTracerouteConfig.load()

    devices_qs = filter_devices_qs_by_user(Devices.objects.all(), request.user)

    if vlan_traceroute_settings.vlan_start:
        devices_names = tuple(map(str.strip, vlan_traceroute_settings.vlan_start.split("\n")))
        devices_qs = devices_qs.filter(name__in=devices_names)
    if vlan_traceroute_settings.vlan_start_regex:
        devices_qs = devices_qs.filter(name__iregex=vlan_traceroute_settings.vlan_start_regex)
    if vlan_traceroute_settings.ip_pattern:
        devices_qs = devices_qs.filter(ip__iregex=vlan_traceroute_settings.ip_pattern)

    tracert = MultipleVlanTraceroute(
        finder=VlanTraceroute(cache_timeout=vlan_traceroute_settings.cache_timeout),
        devices_queryset=devices_qs,
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
        return Response(
            {
                "nodes": [],
                "edges": [],
                "options": {},
            }
        )

    network = VlanNetwork(network=Network(height="100%", width="100%", bgcolor="#222222", font_color="white"))

    network.create_network(result, show_admin_down_ports=only_admin_up)

    return Response(
        {
            "nodes": network.nodes,
            "edges": network.edges,
            "options": orjson.loads(network.options.to_json()),
        }
    )
