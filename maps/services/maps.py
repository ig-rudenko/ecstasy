from django.db.models import QuerySet
from requests import RequestException
from rest_framework.exceptions import APIException

from devicemanager.device import zabbix_api
from maps.models import Maps, Layers
from .layers import get_zabbix_layer_data, get_file_layer_data
from .map_alerts import get_group_problems


def get_map_layers_geo_data(map_object: Maps) -> list[dict]:
    """Возвращает список гео данных для каждого слоя карты."""
    layers_data = []

    try:
        with zabbix_api.connect() as zbx_session:
            for layer in map_object.layers.all():  # Проходимся по введенным именам групп
                if layer.type == "zabbix":
                    layer_data = get_zabbix_layer_data(zbx_session, layer)
                    if layer_data:
                        layers_data.append(layer_data)

                elif layer.type == "file":
                    layer_data = get_file_layer_data(layer)
                    if layer_data:
                        layers_data.append(layer_data)

    except RequestException:
        raise APIException({"detail": "Не удалось подключиться к Zabbix API"})

    return layers_data  # Возвращаем список геообъектов


def get_zabbix_problems_on_map(map_object: Maps) -> list[dict]:
    """Возвращает список текущих проблем для каждой zabbix группы на карте по каждому слою."""

    layers: QuerySet[Layers] = map_object.layers.all()
    groups = layers.values_list("zabbix_group_name", flat=True)
    problems: list[dict] = []

    try:
        with zabbix_api.connect() as zbx_session:
            for group_name in groups:
                if group_name is not None:
                    problems += get_group_problems(zbx_session, group_name)

    except RequestException:
        raise APIException({"detail": "Не удалось подключиться к Zabbix API"})

    return problems
