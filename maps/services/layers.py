import re

import orjson
from django.template.loader import render_to_string
from pyzabbix.api import ZabbixAPI

from app_settings.models import ZabbixConfig
from maps.models import Layers


def get_zabbix_layer_data(zbx_session: ZabbixAPI, layer: Layers) -> dict:
    """
    Эта функция извлекает данные для слоя Zabbix и возвращает их в формате словаря
    со следующими ключами и значениями:

    - "name": имя группы Zabbix, связанной с данным слоем
    - "type": строка, указывающая, что данные взяты из Zabbix
    - "features": словарь, содержащий данные, полученные из Zabbix для данного слоя.
     Если группа Zabbix существует, ключ «features» будет содержать данные.

    :param zbx_session: Объект ZabbixAPI.
    :param layer: Объект слоя Zabbix.
    :return: Словарь со следующими ключами и значениями: "name", "type", "features".
    """

    # Находим группу в Zabbix
    group = zbx_session.hostgroup.get(filter={"name": layer.zabbix_group_name})

    features: dict = {}
    if group and layer.zabbix_group_name is not None:  # Если такая группа существует
        # Добавление результата функции `zabbix_get` в список `geo_json["features"]`
        features = get_zbx_group_data(
            zbx_session,
            group_id=int(group[0]["groupid"]),
            group_name=layer.zabbix_group_name,
            current_layer=layer,
        )

    return {
        "name": layer.zabbix_group_name,
        "type": "zabbix",
        "features": features,
    }


def get_file_layer_data(layer: Layers) -> dict:
    """
    Функция принимает объект слой и возвращает словарь, содержащий данные о стиле
    и функциях для файла слоя в формате GEOJSON.

    :param layer: :class:`Layers`, содержит информацию об определенном слое на карте.
    :return: Словарь, содержащий информацию о слое, включая его имя, тип, свойства
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


def get_zbx_group_data(zbx_session: ZabbixAPI, group_id: int, group_name: str, current_layer: Layers) -> dict:
    """
    Эта функция извлекает данные для указанной группы Zabbix, включая информацию
    о хосте и данные о местоположении, и возвращает их в формате GEOJSON.

    :param zbx_session: Объект ZabbixAPI.
    :param group_id: ID группы Zabbix, для которой нужно получить данные.
    :param group_name: Имя группы Zabbix, для которой функция извлекает данные.
    :param current_layer: Параметр current_layer — это переменная типа данных Layers,
     которая передается функции в качестве аргумента. Он используется для определения
     слоя карты, на котором будут отображаться данные.
    :return: Словарь, содержащий ключ "type" со значением "FeatureCollection"
     и ключ "features" со списком словарей в качестве значения. Каждый словарь в списке
     «features» представляет хост Zabbix и содержит информацию о его расположении и свойствах.
    """
    features: list[dict] = []

    hosts = zbx_session.host.get(
        groupids=group_id,
        output=["description", "name", "status"],
        selectInterfaces=["ip"],
        selectInventory="extend",
    )

    for host in hosts:
        if not _is_valid_zbx_host(host):
            continue

        host["interfaces"] = set(
            map(
                lambda x: x["ip"],
                filter(
                    lambda x: x["ip"] != "127.0.0.1",
                    host["interfaces"],
                ),
            )
        )

        features.append(
            {
                "type": "Feature",
                "id": host["hostid"],
                "geometry": _get_geometry_for_zbx_host(host),
                "properties": _get_properties_for_zbx_host(host, group_name, current_layer),
            }
        )

    return {"type": "FeatureCollection", "features": features}


def _is_valid_zbx_host(host: dict) -> bool:
    """
    Функция проверяет, является ли хост Zabbix валидным на основании его свойств.
    """
    return (
        host["inventory"]
        and host["inventory"]["location_lat"]
        and host["inventory"]["location_lon"]
        and host["status"] == "0"
    )


def _get_geometry_for_zbx_host(host: dict) -> dict:
    """Функция возвращает метку с координатами для хоста Zabbix."""
    return {
        "type": "Point",
        "coordinates": [
            host["inventory"]["location_lon"].replace(",", "."),
            host["inventory"]["location_lat"].replace(",", "."),
        ],
    }


def _get_properties_for_zbx_host(host: dict, group_name: str, current_layer: Layers) -> dict:
    """
    Функция принимает хост Zabbix и возвращает словарь, содержащий информацию о свойствах хоста.

    :param host: Хост Zabbix.
    :param group_name: Название группы, в которой хост находится.
    :param current_layer: :class:`Layers`, содержит информацию об определенном слое на карте.
    :return: Словарь, содержащий информацию о свойствах хоста.
    """
    return {
        "name": host["name"],
        "description": _get_description_for_zbx_host(host),
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


def _get_description_for_zbx_host(host: dict) -> str:
    """
    Функция принимает хост Zabbix и возвращает описание хоста.

    :param host: Хост Zabbix.
    :return: Описание хоста.
    """

    if host.get("description"):
        host["description"] = re.sub(
            r"https?://\S+",
            r'<a target="_blank" href="\g<0>">\g<0></a>',
            host["description"],
        )

    return render_to_string(
        "maps/zbx_popup.html",
        {
            "zbx_settings": ZabbixConfig.load(),
            "host": host,
        },
    )
