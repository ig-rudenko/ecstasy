from datetime import datetime

import orjson
from pyzabbix import ZabbixAPI
from django.template.loader import render_to_string
from requests import RequestException
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from devicemanager.device import ZabbixAPIConnection
from app_settings.models import ZabbixConfig
from maps.models import Maps, Layers
from .permissions import MapPermission
from .serializers import MapLayerSerializer


class MapLayersListAPIView(generics.RetrieveAPIView):
    queryset = Maps.objects.all()
    lookup_url_kwarg = "map_id"
    lookup_field = "id"
    permission_classes = [IsAuthenticated, MapPermission]
    serializer_class = MapLayerSerializer


class ZabbixSessionMixin:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._zbx_settings = ZabbixConfig.load()
        self._zbx_session = None

    def get_zbx_session(self) -> ZabbixAPI:
        if self._zbx_session is None:
            self._zbx_session = ZabbixAPIConnection().connect()
        return self._zbx_session

    def __del__(self, *args, **kwargs):
        if self._zbx_session:
            self._zbx_session.user.logout()


class InteractiveMapAPIView(ZabbixSessionMixin, generics.RetrieveAPIView):
    queryset = Maps.objects.all()
    lookup_url_kwarg = "map_id"
    lookup_field = "id"
    permission_classes = [IsAuthenticated, MapPermission]

    def retrieve(self, request, *args, **kwargs) -> Response:
        """
        Эта функция извлекает данные из слоев объекта карты и возвращает их в формате списка.
        """
        map_obj = self.get_object()

        layers_data = []

        for layer in map_obj.layers.all():  # Проходимся по введенным именам групп
            if layer.type == "zabbix":
                layer_data = self.get_zabbix_layer_data(layer)
                if layer_data:
                    layers_data.append(layer_data)

            elif layer.type == "file":
                layer_data = self.get_file_layer_data(layer)
                if layer_data:
                    layers_data.append(layer_data)

        return Response(layers_data)

    def get_zabbix_layer_data(self, layer: Layers) -> dict:
        """
        Эта функция извлекает данные для слоя Zabbix и возвращает их в формате словаря
        со следующими ключами и значениями:

        - "name": имя группы Zabbix, связанной с данным слоем
        - "type": строка, указывающая, что данные взяты из Zabbix
        - "features": словарь, содержащий данные, полученные из Zabbix для данного слоя.
         Если группа Zabbix существует, ключ «features» будет содержать данные
        """
        layer_data = {
            "name": layer.zabbix_group_name,
            "type": "zabbix",
            "features": {},
        }
        try:
            zbx = self.get_zbx_session()
        except RequestException:
            return {}

        # Находим группу в Zabbix
        group = zbx.hostgroup.get(filter={"name": layer.zabbix_group_name})

        if group:  # Если такая группа существует
            # Добавление результата функции `zabbix_get` в список `geo_json["features"]`
            layer_data["features"] = self.get_zbx_group_data(
                group_id=int(group[0]["groupid"]),
                group_name=layer.zabbix_group_name,
                current_layer=layer,
            )
        return layer_data

    def get_zbx_group_data(self, group_id: int, group_name: str, current_layer: Layers) -> dict:
        """
        Эта функция извлекает данные для указанной группы Zabbix, включая информацию
        о хосте и данные о местоположении, и возвращает их в формате GEOJSON.

        :param group_id: ID группы Zabbix, для которой нужно получить данные.
        :param group_name: Имя группы Zabbix, для которой функция извлекает данные.
        :param current_layer: Параметр current_layer — это переменная типа данных Layers,
         которая передается функции в качестве аргумента. Он используется для определения
         слоя карты, на котором будут отображаться данные.
        :return: словарь, содержащий ключ "type" со значением "FeatureCollection"
         и ключ "features" со списком словарей в качестве значения. Каждый словарь в списке
         «features» представляет хост Zabbix и содержит информацию о его расположении и свойствах.
        """
        result = {"type": "FeatureCollection", "features": []}

        try:
            zbx = self.get_zbx_session()
        except RequestException:
            return {}

        hosts = zbx.host.get(
            groupids=group_id,
            selectInterfaces=["ip"],
            selectInventory=["location_lat", "location_lon"],
        )

        for host in hosts:
            if not self._is_valid_zbx_host(host):
                continue

            result["features"].append(
                {
                    "type": "Feature",
                    "id": host["hostid"],
                    "geometry": self._get_geometry_for_zbx_host(host),
                    "properties": self._get_properties_for_zbx_host(
                        host, group_name, current_layer
                    ),
                }
            )

        return result

    @staticmethod
    def _is_valid_zbx_host(host: dict) -> bool:
        return (
            host["inventory"]
            and host["inventory"]["location_lat"]
            and host["inventory"]["location_lon"]
            and host["status"] == "0"
        )

    @staticmethod
    def _get_geometry_for_zbx_host(host: dict) -> dict:
        return {
            "type": "Point",
            "coordinates": [
                host["inventory"]["location_lon"].replace(",", "."),
                host["inventory"]["location_lat"].replace(",", "."),
            ],
        }

    def _get_properties_for_zbx_host(
        self, host: dict, group_name: str, current_layer: Layers
    ) -> dict:
        return {
            "name": host["name"],
            "description": self._get_description_for_zbx_host(host),
            "group": group_name,
            "figure": "circle",
            "iconName": current_layer.marker_icon_name,
            "style": {
                "radius": current_layer.points_size,
                "fillColor": current_layer.points_color,
                "color": current_layer.points_border_color,
                "weight": 1,
                "opacity": 1,
                "fillOpacity": 1,
            },
        }

    def _get_description_for_zbx_host(self, host: dict) -> str:
        return render_to_string(
            "maps/zbx_popup.html",
            {
                "zbx_settings": self._zbx_settings,
                "host": host,
            },
        )

    @staticmethod
    def get_file_layer_data(layer: Layers) -> dict:
        """
        Функция принимает объект слой и возвращает словарь, содержащий данные о стиле
        и функциях для файла слоя в формате GEOJSON.

        :param layer: Параметр `layer` является экземпляром класса `Layers`, который
         содержит информацию об определенном слое на карте.
        :return: словарь, содержащий информацию о слое, включая его имя, тип, свойства
         стиля для полигонов и маркеров, а также функции (данные) из файла, связанного
         со слоем. Если файл не может быть прочитан, возвращается пустой словарь.
        """

        layer_data = {
            "name": layer.name,
            "type": "geojson",
            "properties": {
                "Polygon": {
                    "FillColor": layer.polygon_fill_color,
                    "Color": layer.polygon_border_color,
                    "Opacity": layer.polygon_opacity,
                },
                "Marker": {
                    "FillColor": layer.points_color,
                    "BorderColor": layer.points_border_color,
                    "Size": layer.points_size,
                    "IconName": layer.marker_icon_name,
                },
            },
            "features": {},
        }

        try:
            # Читаем содержимое файла
            with layer.from_file.open("r") as file:
                try:
                    layer_data["features"] = orjson.loads(file.read())
                except orjson.JSONDecodeError:
                    # Пропускаем файл, который не получилось прочитать
                    return {}
        except FileNotFoundError:
            return {}

        return layer_data


class UpdateInteractiveMapAPIView(ZabbixSessionMixin, generics.RetrieveAPIView):
    queryset = Maps.objects.all()
    lookup_url_kwarg = "map_id"
    lookup_field = "id"
    permission_classes = [IsAuthenticated, MapPermission]

    def retrieve(self, request, *args, **kwargs) -> Response:
        """
        # Проверяем какие из узлов сети недоступны на интерактивной карте с заданным идентификатором

        Возвращаем JSON ответ с проблемными узлами сети и подтверждение проблем (если они есть в Zabbix):

            {
                "problems": [
                    {"id": "host_id", "acknowledges": [["datetime", "text"], ... ]},
                    {"id": "host_id", "acknowledges": [["datetime", "text"], ... ]},
                    ...
                ]

            }
        """

        map_obj: Maps = self.get_object()

        groups = map_obj.layers.all().values_list("zabbix_group_name", flat=True)
        problem_hosts = []
        for group_name in groups:
            problem_hosts += self.get_group_problems(group_name)

        return Response({"problems": problem_hosts})

    def get_group_problems(self, group_name: str) -> list:
        """
        Эта функция возвращает список проблем для данной группы хостов Zabbix, если она существует.

        :param group_name: Строка, представляющая имя группы Zabbix.
        """
        try:
            zbx = self.get_zbx_session()
        except RequestException:
            return []

        group = zbx.hostgroup.get(filter={"name": group_name})
        if group:  # Если такая группа существует
            return self.get_hosts_problems(zabbix_group_id=group[0]["groupid"])
        else:
            return []

    def get_hosts_problems(self, zabbix_group_id: str) -> list:
        """
        Определяет недоступные узлы сети для конкретной группы Zabbix, а также их подтверждения проблем.
        :param zabbix_group_id: ID Группы в Zabbix
        :return: Список из ID тех узлов, которые недоступны в этой группе и подтверждения по этим проблемам
        """

        try:
            zbx = self.get_zbx_session()
        except RequestException:
            return []

        hosts_id = [
            host["hostid"]
            # Получение всех хостов в группе с заданным идентификатором группы.
            for host in zbx.host.get(
                groupids=[zabbix_group_id], output=["hostid"], filter={"status": "0"}
            )
        ]

        # Получение проблемы узла сети из Zabbix.
        hosts_problems_list = zbx.problem.get(
            hostids=hosts_id,
            selectAcknowledges="extend",
            output="extend",
            filter={"name": "Оборудование недоступно"},
        )

        # Перебор списка проблем.
        problems = [self.get_host_acknowledges(problem) for problem in hosts_problems_list]
        return problems

    def get_host_acknowledges(self, problem: dict) -> dict:
        """
        Эта функция извлекает подтверждения для данного сетевого узла с проблемой.

        :param problem: Словарь, содержащий информацию о проблеме в сетевом узле
        :return: Словарь, содержащий идентификатор сетевого узла с проблемой и
         список подтверждений (если есть) для этой проблемы.
        """
        # ID узла сети, у которого проблема.

        try:
            zbx = self.get_zbx_session()
        except RequestException:
            return {}

        host_id = zbx.item.get(triggerids=[problem["objectid"]], output=["hostid", "name"])

        acknowledges = [
            [
                ack["message"],
                datetime.fromtimestamp(int(ack["clock"])).strftime("%H:%M %d-%m-%Y"),
            ]
            for ack in problem["acknowledges"]
        ]

        return {"id": host_id[0]["hostid"], "acknowledges": acknowledges}
