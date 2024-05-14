from django.core.cache import cache
from pyzabbix.api import ZabbixAPI


def get_device_zabbix_maps_ids(zbx_session: ZabbixAPI, host_id: int | str) -> list[dict[str, str]]:
    """
    Возвращает список карт Zabbix, в которых находится узел сети Zabbix по его id.
    """
    hosts_map_ids: list[dict[str, str]] = []
    if not host_id:
        return []

    for map_ in get_all_zabbix_maps_list(zbx_session):
        if not map_.get("sysmapid"):
            continue

        for element in map_.get("selements", []):
            for host in element.get("elements", []):
                if host.get("hostid") == str(host_id):
                    hosts_map_ids.append(
                        {
                            "sysmapid": int(map_.get("sysmapid")),  # ID карты
                            "name": map_.get("name", "Без названия"),  # Название карты
                        },
                    )
    return hosts_map_ids


def get_all_zabbix_maps_list(zbx_session: ZabbixAPI) -> list:
    """
    Возвращает список всех zabbix карт.
    [{'name': 'Название карты', 'sysmapid': '94', 'elements': [ {'elements': [{'hostid': '11469'}]},... ]}]
    :return: Список.
    """

    cache_key = "zabbix_maps"
    cached_data: list | None = cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    map_data: list = zbx_session.map.get(selectSelements=["elements"], output=["sysmapid", "name"])

    cache.set(cache_key, map_data, timeout=60 * 10)
    return map_data
