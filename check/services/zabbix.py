from pyzabbix.api import ZabbixAPI, ZabbixAPIException
from requests.exceptions import RequestException
from urllib3.exceptions import MaxRetryError

from devicemanager.device.zabbix_api import zabbix_api
from ecstasy_project.decorators import cached


@cached(60 * 10, key=lambda _, host_id: f"device_zabbix_maps_ids:{host_id}")
def get_device_zabbix_maps_ids(zbx_session: ZabbixAPI, host_id: int | str) -> list[dict[str, str | int]]:
    """
    Возвращает список карт Zabbix, в которых находится узел сети Zabbix по его id.
    """
    hosts_map_ids: list[dict[str, str | int]] = []
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
                            "sysmapid": int(map_["sysmapid"]),  # ID карты
                            "name": map_.get("name", "Без названия"),  # Название карты
                        },
                    )
    return hosts_map_ids


@cached(60 * 10, key="zabbix_maps")
def get_all_zabbix_maps_list(zbx_session: ZabbixAPI) -> list:
    """
    Возвращает список всех zabbix карт.
    [{'name': 'Название карты', 'sysmapid': '94', 'elements': [ {'elements': [{'hostid': '11469'}]},... ]}]
    :return: Список.
    """
    return zbx_session.map.get(selectSelements=["elements"], output=["sysmapid", "name"])


@cached(90, key=lambda _, host_id: f"device_uptime:{host_id}")
def get_device_uptime(zbx_session: ZabbixAPI, host_id: int | str) -> int:
    """Возвращает время работы устройства"""
    try:
        uptime_items = zbx_session.item.get(hostids=host_id, output=["itemid"], search={"key_": "uptime"})
        for item in uptime_items:
            uptime_value = zbx_session.history.get(
                itemids=item["itemid"], output=["value"], history=3, limit=1
            )
            if uptime_value:
                return uptime_value[0]["value"]
    except (MaxRetryError, RequestException):
        pass
    return -1


@cached(60, key=lambda name: f"zabbix_graphs:{name}")
def get_zabbix_graphs(device_name: str) -> tuple[int, list]:
    graphs = []
    host_id = 0
    try:
        with zabbix_api.connect() as zbx:
            host = zbx.host.get(output=["name"], filter={"name": device_name})
            if not host:
                return host_id, []

            # Получаем все графики для данного узла сети.
            host_id = host[0]["hostid"]

            graphs = zbx.graph.get(hostids=[host_id])
    except (MaxRetryError, RequestException) as exc:
        print(f"Ошибка `collect_zabbix_graphs` {exc}")
    return host_id, graphs


@cached(60 * 10, key=lambda host_id: f"zabbix_map_and_uptime:{host_id}")
def get_zabbix_host_map_and_uptime(host_id: int | str) -> tuple[list[dict[str, str | int]], int]:
    with zabbix_api.connect() as zbx:
        devices_maps = get_device_zabbix_maps_ids(zbx, host_id)
        uptime = get_device_uptime(zbx, host_id)
    return devices_maps, uptime


@cached(20, key=lambda device_name: f"zabbix_info:{device_name}")
def get_zabbix_host_info(device_name: str) -> dict:
    try:
        print(zabbix_api)
        with zabbix_api.connect() as zbx:
            info = zbx.host.get(
                filter={"name": device_name},
                output=["hostid", "host", "name", "status", "description"],
                selectGroups=["groupid", "name"],
                selectInterfaces=["ip"],
                selectInventory="extend",
            )
            if len(info) > 0:
                return info[0]
    except (MaxRetryError, RequestException, ZabbixAPIException):
        pass
    return {}
