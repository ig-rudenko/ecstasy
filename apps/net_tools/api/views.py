from django.conf import settings
from requests import RequestException
from rest_framework.request import Request
from rest_framework.response import Response

from apps.app_settings.models import ZabbixConfig
from apps.check.models import Devices
from apps.check.services.filters import filter_devices_qs_by_user
from devicemanager.device import zabbix_api
from ecstasy_project.types.api import UserAuthenticatedAPIView

from ..models import VlanName
from ..services.arp_find import collect_ip_mac_info_ips, find_mac_or_ip, get_ecstasy_devices_by_ip
from ..services.interface_finder.finder import InterfacesFinder
from ..services.interface_finder.types import InterfaceFinderFilter
from ..services.mac_finder import get_mac_info
from ..services.traceroute.graph import build_traceroute_graph_data, build_traceroute_map_data
from .permissions import InterfaceFinderPermission, TracerouteAccessPermission, WTFSearchPermission
from .queries import InterfaceFinderQuerySerializer
from .serializers import GetVlanDescQuerySerializer, TracerouteMapQuerySerializer, TracerouteQuerySerializer
from .swagger.schemas import (
    find_by_description_schema,
    get_vendor_schema,
    get_vlan_desc_schema,
    traceroute_map_schema,
    traceroute_schema,
)


class GetVendorByMacAPIView(UserAuthenticatedAPIView):
    """
    Определяет производителя оборудования по MAC-адресу через внешний сервис.
    """

    @get_vendor_schema
    def get(self, request: Request, mac: str) -> Response:
        info = get_mac_info(mac, proxy=settings.PROXY_URL)
        return Response(
            {
                "vendor": info.vendor,
                "address": info.address,
            }
        )


class InterfaceFinderAPIView(UserAuthenticatedAPIView):
    """
    Выполняет поиск интерфейсов по описанию и комментариям, с поддержкой обычного текста и регулярных выражений.
    """

    permission_classes = [InterfaceFinderPermission]

    @find_by_description_schema
    def get(self, request: Request, *args, **kwargs):
        query_filter = self._get_query()

        devices_qs = filter_devices_qs_by_user(Devices.objects.all(), self.current_user)

        finder = InterfacesFinder(devices_qs, query_filter)
        result = finder.find_description()

        return Response({"interfaces": result, "count": len(result)})

    def _get_query(self) -> InterfaceFinderFilter:
        serializer = InterfaceFinderQuerySerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)
        return serializer.create(serializer.validated_data)


class ARPSearchAPIView(UserAuthenticatedAPIView):
    """
    Выполняет распределённый ARP-поиск по IP или MAC и дополняет результат данными из Zabbix.
    """

    permission_classes = [WTFSearchPermission]

    def get(self, request, ip_or_mac: str):
        arp_info = find_mac_or_ip(ip_or_mac)
        found_ips = collect_ip_mac_info_ips(ip_or_mac, arp_info)

        zabbix_url = ZabbixConfig.load().url

        names = []
        if len(arp_info) > 0:
            ips = [line.ip for info in arp_info for line in info.results]

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

        ecstasy_devices = get_ecstasy_devices_by_ip(found_ips, self.current_user)
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

        return Response(
            {
                "info": arp_info_json,
                "zabbix": names,
                "zabbix_url": zabbix_url,
                "ecstasy_devices": ecstasy_devices,
            }
        )


class VlanNameAPIView(UserAuthenticatedAPIView):
    """
    Возвращает название и описание VLAN по его идентификатору.
    """

    permission_classes = [TracerouteAccessPermission]

    @get_vlan_desc_schema
    def get(self, request: Request) -> Response:
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


class TracerouteAPIView(UserAuthenticatedAPIView):
    """
    Строит граф трассировки сети для поиска по VLAN или по MAC, включая узлы, связи и параметры отображения.
    """

    @traceroute_schema
    def get(self, request: Request) -> Response:
        serializer = TracerouteQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        graph_data = build_traceroute_graph_data(self.current_user, serializer.validated_data)
        return Response(graph_data)


class TracerouteMapAPIView(UserAuthenticatedAPIView):
    """
    Строит географическую визуализацию трассировки сети по координатам узлов из Zabbix.
    """

    @traceroute_map_schema
    def get(self, request: Request) -> Response:
        serializer = TracerouteMapQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        graph_data = build_traceroute_graph_data(self.current_user, serializer.validated_data)
        return Response(build_traceroute_map_data(graph_data))
