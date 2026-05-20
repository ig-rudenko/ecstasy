import re
from functools import reduce

import requests as requests_lib
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.cache import cache
from django.http import HttpResponse
from requests import RequestException
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from apps.app_settings.models import ZabbixConfig
from apps.check.models import Devices
from apps.check.services.filters import filter_devices_qs_by_user
from devicemanager.device import zabbix_api
from ecstasy_project.error_handler import ExternalServiceProblem

from ..models import VlanName
from ..services.arp_find import find_mac_or_ip
from ..services.finder import DescriptionFinder
from ..services.traceroute import build_traceroute_graph_data, build_traceroute_map_data
from ..tasks import check_scanning_status, interfaces_scan
from .serializers import GetVlanDescQuerySerializer, TracerouteMapQuerySerializer, TracerouteQuerySerializer
from .swagger.schemas import (
    find_by_description_schema,
    get_vendor_schema,
    get_vlan_desc_schema,
    traceroute_map_schema,
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
    """
    Возвращает текущее состояние фоновой задачи периодического сканирования интерфейсов.
    """
    return Response(check_scanning_status())


@get_vendor_schema
@api_view(["GET"])
@login_required
def get_vendor(request: Request, mac: str) -> Response:
    """
    Определяет производителя оборудования по MAC-адресу через внешний сервис.
    """
    proxies = {}
    if settings.PROXY_URL:
        proxies = {"http": settings.PROXY_URL, "https": settings.PROXY_URL}
    try:
        resp = requests_lib.get("https://api.maclookup.app/v2/macs/" + mac, timeout=2, proxies=proxies)
    except requests_lib.RequestException as exc:
        raise ExternalServiceProblem(
            {"detail": "MAC vendor lookup service is unavailable.", "mac": mac}
        ) from exc

    if resp.status_code == 400:
        raise ValidationError({"mac": resp.json().get("error", "Invalid MAC")})
    if resp.status_code != 200:
        raise ValidationError({"mac": "Invalid MAC"})

    data = resp.json()
    return Response(
        {
            "vendor": data.get("company", "Unknown"),
            "address": data.get("address", "Unknown"),
        }
    )


@find_by_description_schema
@api_view(["GET"])
@login_required
@permission_required(perm="auth.access_desc_search", raise_exception=True)
def find_by_description(request):
    """
    Выполняет поиск интерфейсов по описанию и комментариям, с поддержкой обычного текста и регулярных выражений.
    """
    is_regex = request.GET.get("is_regex", "0").lower() in ("1", "true")
    pattern = request.GET.get("pattern", "")
    if not pattern:
        return Response({"interfaces": []})

    if is_regex:
        try:
            re.compile(pattern)
        except re.PatternError as exc:
            raise ValidationError({"pattern": f"Regex error: {exc}"}) from exc

    devices_qs = filter_devices_qs_by_user(Devices.objects.all(), request.user)
    finder = DescriptionFinder(devices_qs)
    result = finder.find_description(pattern_str=pattern, is_regex=is_regex)

    return Response({"interfaces": result})


@api_view(["GET"])
@login_required
@permission_required(perm="auth.access_wtf_search", raise_exception=True)
def ip_mac_info(request, ip_or_mac: str):
    """
    Выполняет распределённый ARP-поиск по IP или MAC и дополняет результат данными из Zabbix.
    """
    arp_info = find_mac_or_ip(ip_or_mac)

    zabbix_url = ZabbixConfig.load().url

    names = []
    if len(arp_info) > 0:
        ips = reduce(lambda x, y: x + y, map(lambda r: [line.ip for line in r.results], arp_info))

        try:
            with zabbix_api.connect() as zbx:
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
    Возвращает название и описание VLAN по его идентификатору.
    """
    serializer = GetVlanDescQuerySerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)

    data = {"name": "", "description": ""}

    try:
        vlan: VlanName = VlanName.objects.get(vid=serializer.validated_data["vlan"])
    except VlanName.DoesNotExist:
        pass
    else:
        data = {"name": vlan.name or "", "description": vlan.description}

    return Response(data)


@vlan_traceroute_schema
@api_view(["GET"])
@login_required
@permission_required(perm="auth.access_traceroute", raise_exception=True)
def get_traceroute(request: Request) -> Response:
    """
    Строит граф трассировки сети для поиска по VLAN или по MAC, включая узлы, связи и параметры отображения.
    """
    serializer = TracerouteQuerySerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    graph_data = build_traceroute_graph_data(request, serializer.validated_data)
    return Response(graph_data)


@traceroute_map_schema
@api_view(["GET"])
@login_required
@permission_required(perm="auth.access_traceroute", raise_exception=True)
def get_traceroute_map(request: Request) -> Response:
    """
    Строит географическую визуализацию трассировки сети по координатам узлов из Zabbix.
    """
    serializer = TracerouteMapQuerySerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    graph_data = build_traceroute_graph_data(request, serializer.validated_data)
    return Response(build_traceroute_map_data(graph_data))
