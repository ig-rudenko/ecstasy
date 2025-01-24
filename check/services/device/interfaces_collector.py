import re
from datetime import datetime
from typing import TypeVar, TypedDict

import orjson
from django.utils import timezone
from requests import RequestException

from check.logger import django_actions_logger
from check.models import Devices
from devicemanager.device import DeviceManager, zabbix_api
from devicemanager.zabbix_info_dataclasses import ZabbixInventory
from net_tools.models import DevicesInfo


class DeviceInterfacesGather:
    def __init__(self, device: Devices, device_collector: DeviceManager, with_vlans: bool) -> None:
        self.device = device
        self.device_collector = device_collector

        # Поля для обновлений, в случае изменения записи в БД
        self.model_update_fields: list[str] = []

        # Собирать вместе с VLAN
        self.with_vlans = with_vlans

    def collect_current_interfaces(self, make_session_global: bool) -> None:
        """
        ## Собираем список всех интерфейсов на устройстве в данный момент.

        Если при подключении логин/пароль неверные, то пробуем другие группы авторизации
        """

        # Собираем интерфейсы
        self.device_collector.collect_interfaces(
            vlans=self.with_vlans,
            current_status=True,
            raise_exception=True,
            make_session_global=make_session_global,
        )
        if self.device.interface_pattern:
            self.device_collector.interfaces = self.device_collector.interfaces.filter_by_name(
                self.device.interface_pattern
            )

    def get_last_interfaces(self) -> tuple[list, datetime]:
        """
        ## Возвращает кортеж из последних собранных интерфейсов и времени их последнего изменения.

            (
                [ { "Interface": "GE0/0/2", "Status": "down", "Description": "desc" }, ... ] ,
                datetime
            )
        """

        interfaces: list = []
        collected_time: datetime = timezone.now()

        try:
            device_info = DevicesInfo.objects.get(dev=self.device)
        except DevicesInfo.DoesNotExist:
            return interfaces, collected_time

        # Если необходимы интерфейсы с VLAN и они имеются в БД, то отправляем их
        if self.with_vlans and device_info.vlans:
            interfaces = orjson.loads(device_info.vlans or "[]")
            collected_time = device_info.vlans_date or timezone.now()
        else:
            interfaces = orjson.loads(device_info.interfaces or "[]")
            collected_time = device_info.interfaces_date or timezone.now()

        return interfaces, collected_time


class DeviceDBSynchronizer(DeviceInterfacesGather):
    def sync_device_info_to_db(self) -> None:
        """
        ## Обновляем информацию об устройстве (вендор, модель, серийный номер) в БД.
        """
        actual_inventory: ZabbixInventory = self.device_collector.zabbix_info.inventory

        if self.device_collector.zabbix_info.inventory.model != self.device.model:
            self.device.model = actual_inventory.model
            self.model_update_fields.append("model")

        if self.device_collector.zabbix_info.inventory.vendor != self.device.vendor:
            self.device.vendor = actual_inventory.vendor
            self.model_update_fields.append("vendor")

        if self.device_collector.zabbix_info.inventory.serialno_a != self.device.serial_number:
            self.device.serial_number = actual_inventory.serialno_a
            self.model_update_fields.append("serial_number")

        # Сохраняем изменения
        if self.model_update_fields:
            self.device.save(update_fields=self.model_update_fields)

    def save_interfaces_to_db(self):
        """
        ## Сохраняем интерфейсы в БД
        :return: Список сохраненных интерфейсов
        """
        device_info, _ = DevicesInfo.objects.get_or_create(dev=self.device)
        if self.device_collector.interfaces and self.with_vlans:
            device_info.update_interfaces_with_vlans_state(self.device_collector.interfaces)
            device_info.save(update_fields=["vlans", "vlans_date"])

        if self.device_collector.interfaces:
            device_info.update_interfaces_state(self.device_collector.interfaces)
            device_info.save(update_fields=["interfaces", "interfaces_date"])


class DeviceInterfacesResult(TypedDict):
    interfaces: list
    deviceAvailable: bool
    collected: datetime


def get_device_interfaces(
    device: Devices,
    device_collector: DeviceManager,
    current_status: bool,
    with_vlans: bool,
    check_status: bool = True,
) -> DeviceInterfacesResult:
    # Проверяем доступность оборудования.
    available = check_status and device.available

    # Если оборудование доступно, то можно собирать интерфейсы в реальном времени.
    current_status = current_status and available

    # Уточняем возможность сбора VLAN интерфейсов.
    # Если интерфейсы опрашиваются через SNMP, то сбор VLAN на интерфейсах не доступен.
    with_vlans = False if device.port_scan_protocol == "snmp" else with_vlans

    device_sync = DeviceDBSynchronizer(
        device=device, device_collector=device_collector, with_vlans=with_vlans
    )

    # Если не нужен текущий статус интерфейсов, то отправляем прошлые данные
    if not current_status:
        last_interfaces, last_datetime = device_sync.get_last_interfaces()

        return {
            "interfaces": last_interfaces,
            "deviceAvailable": available > 0,
            "collected": last_datetime,
        }

    # Собираем состояние интерфейсов оборудования в данный момент.
    device_sync.collect_current_interfaces(make_session_global=True)

    # Синхронизируем реальные данные оборудования и поля в базе.
    device_sync.sync_device_info_to_db()

    # Обновляем данные в Zabbix.
    device_sync.device_collector.push_zabbix_inventory()

    # Если не собрали интерфейсы.
    if not device_sync.device_collector.interfaces:
        # Возвращает пустой список интерфейсов.
        return {
            "interfaces": [],
            "deviceAvailable": bool(available),
            "collected": timezone.now(),
        }

    # Если собирали интерфейсы, то сохраняем их в БД.
    device_sync.save_interfaces_to_db()

    # Далее возвращаем интерфейсы.
    return {
        "interfaces": device_sync.device_collector.interfaces.json(),
        "deviceAvailable": bool(available),
        "collected": timezone.now(),
    }


INTF = TypeVar("INTF", bound=list)


class InterfacesBuilder:
    """
    Добавляет к интерфейсам ссылку на оборудование "Link", которое находится в описании, если есть.
    Добавляет комментарии к интерфейсам, если есть.
    Добавляет графики Zabbix к интерфейсам, если есть.
    """

    def __init__(self, device: Devices):
        self._device = device

    def build(
        self,
        interfaces: INTF,
        add_links: bool = True,
        add_comments: bool = True,
        add_zabbix_graph: bool = True,
    ) -> INTF:
        """Формирует список интерфейсов"""
        if add_links:
            interfaces = self._add_devices_links(interfaces)
        if add_comments:
            interfaces = self._add_comments(interfaces)
        if add_zabbix_graph:
            interfaces = self._add_zabbix_graph_links(interfaces)
        return interfaces

    @staticmethod
    def _add_devices_links(interfaces: INTF) -> INTF:
        """
        ## Добавляет к интерфейсам ссылку на оборудование "Link", которое находится в описании

            {
                "Interface": "te1/0/2",
                "Status": "up",
                "Description": "To_DEVICE-1_pTe0/1|DF|",
                "Link": {
                    "device_name": "DEVICE-1",
                    "url": "/device/DEVICE-1"
                }
            },

        :param interfaces: Список интерфейсов
        :return: Список интерфейсов с добавлением ссылок
        """

        devices_names = Devices.objects.all().values_list("name", flat=True)
        for intf in interfaces:
            for dev_name in devices_names:
                if dev_name in intf["Description"]:
                    intf["Link"] = {
                        "device_name": dev_name,
                        "url": f"/device/{dev_name}",
                    }

        return interfaces

    def _add_comments(self, interfaces: INTF) -> INTF:
        """
        ## Берет список интерфейсов и добавляет к ним существующие комментарии

            {
                "Interface": "Eth0/0/6",
                "Status": "up",
                "Description": "Teplostroy",
                "Comments": [
                    {
                        "text": "Стоит медиаконвертор",
                        "user": "irudenko",
                        "id": 14
                    }
                ]
            },

        :param interfaces: Список интерфейсов для добавления комментариев.
        """

        interfaces_comments = self._device.interfacescomments_set.select_related("user")

        for intf in interfaces:
            intf["Comments"] = [
                {
                    "text": comment.comment,
                    "user": comment.user.username if comment.user else "Anonymous",
                    "id": comment.id,
                    "createdTime": comment.datetime.isoformat(),
                }
                for comment in interfaces_comments
                if comment.interface == intf["Interface"]
            ]

        return interfaces

    def _add_zabbix_graph_links(self, interfaces: INTF) -> INTF:
        try:
            with zabbix_api.connect() as zbx:
                host = zbx.host.get(output=["name"], filter={"name": self._device.name})
                if not host:
                    return interfaces

                # Получаем все графики для данного узла сети.
                host_id = host[0]["hostid"]
                graphs = zbx.graph.get(hostids=[host_id])

            for intf in interfaces:
                intf_pattern = re.compile(rf"\s(Gi0/|1/)?\s?{intf['Interface']}[a-zA-Z\s(]")
                intf_desc = intf["Description"]
                valid_graph_ids = []

                for g in graphs:
                    # Ищем все графики, в которых упоминается description или название интерфейса.
                    if (intf_desc and intf_desc in g["name"]) or intf_pattern.search(g["name"]):
                        valid_graph_ids.append(g["graphid"])

                graphs_ids_params = ""
                # Создаем параметры URL для фильтрации только требуемых графиков.
                for graph_id in valid_graph_ids:
                    graphs_ids_params += f"filter_graphids%5B%5D={graph_id}&"

                if graphs_ids_params:
                    # Создаем ссылку на графики zabbix, если получилось их найти.
                    intf["GraphsLink"] = (
                        f"{zabbix_api.zabbix_url}/zabbix.php?"
                        f"view_as=showgraph&action=charts.view&from=now-24h&to=now&"
                        f"filter_hostids%5B%5D={host_id}&filter_search_type=0&"
                        f"{graphs_ids_params}filter_set=1"
                    )

        except RequestException as exc:
            django_actions_logger.error("Ошибка `add_zabbix_graph_links`", exc_info=exc)
        finally:
            return interfaces
