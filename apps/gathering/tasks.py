import logging
from datetime import timedelta

from celery import shared_task
from celery.result import AsyncResult
from django.core.cache import cache
from django.utils import timezone
from django_celery_beat.models import PeriodicTask
from pyzabbix.api import logger

from apps.check.models import Devices
from apps.check.services.device.interfaces_collector import DeviceDBSynchronizer
from devicemanager import snmp
from devicemanager.dc import DeviceRemoteConnector
from devicemanager.device import DeviceManager, Interfaces
from ecstasy_project.celery import app
from ecstasy_project.celery_schedules import get_crontab_schedule

from .models import DeviceGatheringResult, GatheringTask, MacAddress, Vlan
from .services.collectors import ThreadUpdatedStatusDeviceTask
from .services.configurations import ConfigurationGather, LocalConfigStorage
from .services.mac import MacAddressTableGather
from .services.vlan.collector import VlanTableGather

task_logger = logging.getLogger(__name__)


@shared_task(name="cleanup_gathering_tasks_task")
def cleanup_gathering_tasks_task(retention_days: int) -> dict[str, int]:
    """Удалить старые завершённые запуски сбора вместе с результатами устройств."""

    retention_days = int(retention_days)
    if retention_days < 1:
        raise ValueError("retention_days must be positive")

    cutoff = timezone.now() - timedelta(days=retention_days)
    queryset = GatheringTask.objects.filter(finished_at__lt=cutoff)
    deleted_count = queryset.count()
    queryset.delete()
    return {
        "deletedCount": deleted_count,
        "retentionDays": retention_days,
    }


class MacTablesGatherTask(ThreadUpdatedStatusDeviceTask):
    """
    # Celery задача для сбора таблицы MAC адресов оборудования.

    Использует пул потоков, а затем отправляет задачу на сбор MAC для каждого оборудования в queryset.

    Задача обновляет свой статус после каждого завершенного сбора на оборудовании.
    """

    name = "mac_table_gather_task"
    queryset = Devices.objects.filter(active=True, collect_mac_addresses=True)
    max_workers = 80

    def pre_run(self):
        """
        Он устанавливает ключ кэша с именем «mac_table_gather_task_id» на идентификатор текущей задачи.
        """
        super().pre_run()
        logger.setLevel(logging.ERROR)
        cache.set("mac_table_gather_task_id", self.request.id, timeout=None)

        # Удаляем старые MAC адреса.
        res = MacAddress.objects.filter(datetime__lt=timezone.now() - timedelta(hours=48)).delete()
        task_logger.info("Cleared outdated MAC entries: %s", res)

    def thread_task(self, obj: Devices, **kwargs) -> str:
        """Собрать MAC-адреса устройства и вернуть статус результата."""

        if not obj.available:
            return DeviceGatheringResult.Status.SKIPPED

        with DeviceRemoteConnector(
            ip=obj.ip,
            protocol=obj.cmd_protocol,
            auth_obj=obj.auth_group,
            snmp_community=obj.snmp_community or "",
            telnet_port=obj.telnet_port,
            ssh_port=obj.ssh_port,
            snmp_port=obj.snmp_port,
        ) as session:
            if obj.port_scan_protocol == "snmp":
                interfaces = Interfaces(snmp.get_interfaces(obj.ip, obj.snmp_community, obj.snmp_port))
            else:
                interfaces = Interfaces(session.get_interfaces())

            gather = MacAddressTableGather(obj, session=session, interfaces=interfaces)
            gather.run_gathering()

        self.log(device=obj, message="MAC collected")
        return DeviceGatheringResult.Status.SUCCESS

    @classmethod
    def register_task(cls):
        crontab = get_crontab_schedule(
            minute="0",
            hour="1,3,5,7,9,11,13,15,17,19,21,23",
        )
        PeriodicTask.objects.get_or_create(
            name="Сбор MAC адресов",
            defaults={
                "task": cls.name,
                "crontab": crontab,
                "enabled": False,
            },
        )

    def finish(self):
        """
        Очищает кэш для фильтров в панели администратора.
        """
        cache.delete("admin_device_filter_lookups")
        cache.delete("admin_vlan_filter_lookups")
        cache.delete("admin_type_filter_lookups")
        cache.delete("admin_port_filter_lookups")


class VlanTablesGatherTask(ThreadUpdatedStatusDeviceTask):
    """
    # Celery задача для сбора таблицы VLAN оборудования.

    Использует пул потоков, а затем отправляет задачу на сбор VLAN для каждого оборудования в queryset.

    Задача обновляет свой статус после каждого завершенного сбора на оборудовании.
    """

    name = "vlan_table_gather_task"
    queryset = Devices.objects.filter(active=True, collect_vlan_info=True)
    max_workers = 80

    def pre_run(self):
        """
        Устанавливает ключ кэша с именем "vlan_table_gather_task_id" на идентификатор текущей задачи.
        """
        super().pre_run()
        logger.setLevel(logging.ERROR)
        cache.set("vlan_table_gather_task_id", self.request.id, timeout=None)

        # Удаляем старые VLAN.
        res = Vlan.objects.filter(datetime__lt=timezone.now() - timedelta(hours=48)).delete()
        task_logger.info("Cleared outdated VLAN entries: %s", res)

    def thread_task(self, obj: Devices, **kwargs) -> str:
        """Собрать VLAN устройства и вернуть статус результата."""

        if not obj.available:
            return DeviceGatheringResult.Status.SKIPPED

        with DeviceRemoteConnector(
            ip=obj.ip,
            protocol=obj.cmd_protocol,
            auth_obj=obj.auth_group,
            snmp_community=obj.snmp_community or "",
            telnet_port=obj.telnet_port,
            ssh_port=obj.ssh_port,
            snmp_port=obj.snmp_port,
        ) as session:
            if obj.port_scan_protocol == "snmp":
                interfaces = Interfaces(snmp.get_interfaces(obj.ip, obj.snmp_community, obj.snmp_port))
            else:
                interfaces = Interfaces(session.get_interfaces())

            gather = VlanTableGather(obj, session=session, interfaces=interfaces)
            gather.run_gathering()

        self.log(device=obj, message="VLANS collected")
        return DeviceGatheringResult.Status.SUCCESS

    @classmethod
    def register_task(cls):
        crontab = get_crontab_schedule(
            minute="0",
            hour="2,6,10,14,18,22",  # Сбор через каждые 4 часа
        )
        PeriodicTask.objects.get_or_create(
            name="Сбор VLAN таблиц",
            defaults={
                "task": cls.name,
                "crontab": crontab,
                "enabled": False,
            },
        )


class ConfigurationGatherTask(ThreadUpdatedStatusDeviceTask):
    """
    # Celery задача для сбора таблицы MAC адресов оборудования.

    Использует пул потоков, а затем отправляет задачу на сбор MAC для каждого оборудования в queryset.

    Задача обновляет свой статус после каждого завершенного сбора на оборудовании.
    """

    name = "configuration_gather_task"
    queryset = Devices.objects.filter(active=True, collect_configurations=True)
    max_workers = 40

    def thread_task(self, obj: Devices, **kwargs) -> str:
        """Собрать конфигурацию устройства и вернуть статус результата."""

        storage = LocalConfigStorage(obj)
        gather = ConfigurationGather(storage=storage)
        is_collected = gather.collect_config_file()
        if is_collected:
            gather.delete_outdated_configs()
        self.log(device=obj, message=f"collect_config_file: {is_collected}")
        return DeviceGatheringResult.Status.SUCCESS

    @classmethod
    def register_task(cls):
        crontab = get_crontab_schedule(
            minute="30",
            hour="4",
        )
        PeriodicTask.objects.get_or_create(
            name="Сбор файлов конфигураций",
            defaults={
                "task": cls.name,
                "crontab": crontab,
                "enabled": False,
            },
        )


class DevicesComplexGatherTask(ThreadUpdatedStatusDeviceTask):
    """
    # Celery задача для сбора интерфейсов, таблицы MAC адресов и VLAN оборудования.

    Использует пул потоков, а затем отправляет задачу для каждого оборудования в queryset.

    Задача обновляет свой статус после каждого завершенного сбора на оборудовании.
    """

    name = "devices_complex_gather_task"
    queryset = Devices.objects.filter(active=True)
    max_workers = 80

    def pre_run(self):
        """
        Он устанавливает ключ кэша с именем «mac_table_gather_task_id» на идентификатор текущей задачи.
        """
        super().pre_run()
        logger.setLevel(logging.ERROR)
        cache.set("devices_complex_gather_task_id", self.request.id, timeout=None)

        # Удаляем старые MAC адреса.
        res = MacAddress.objects.filter(datetime__lt=timezone.now() - timedelta(hours=48)).delete()
        task_logger.info("Cleared outdated MAC entries: %s", res)

    def thread_task(self, obj: Devices, **kwargs) -> str:
        """Выполнить комплексный сбор устройства и вернуть статус результата."""

        if not obj.available:
            return DeviceGatheringResult.Status.SKIPPED

        with DeviceRemoteConnector(
            ip=obj.ip,
            protocol=obj.cmd_protocol,
            auth_obj=obj.auth_group,
            snmp_community=obj.snmp_community or "",
            telnet_port=obj.telnet_port,
            ssh_port=obj.ssh_port,
            snmp_port=obj.snmp_port,
        ) as session:
            self._collect(device=obj, session=session)

        return DeviceGatheringResult.Status.SUCCESS

    def _collect(self, device: Devices, session):
        interfaces_desc = None

        # INTERFACE GATHERING
        synchronizer = DeviceDBSynchronizer(
            device=device,
            device_collector=DeviceManager.from_model(device),
            with_vlans=True,
        )
        interfaces = synchronizer.collect_current_interfaces(make_session_global=False)
        synchronizer.sync_device_info_to_db()
        synchronizer.device_collector.push_zabbix_inventory()
        synchronizer.save_interfaces_to_db()
        self.log(device=device, message="Интерфейсы успешно обновлены")

        # MAC GATHERING
        if device.collect_mac_addresses:
            mac_gather = MacAddressTableGather(device, session=session, interfaces=interfaces)
            mac_gather.run_gathering()
            self.log(device=device, message="MAC адреса собраны")
            interfaces_desc = mac_gather.interfaces_desc

        # VLAN GATHERING
        if device.collect_vlan_info:
            vlan_gather = VlanTableGather(
                device, session=session, interfaces=interfaces, interfaces_desc=interfaces_desc
            )
            vlan_gather.run_gathering()
            self.log(device=device, message="VLAN собраны")

    @classmethod
    def register_task(cls):
        crontab = get_crontab_schedule(
            minute="0",
            hour="1,3,5,7,9,11,13,15,17,19,21,23",
        )
        PeriodicTask.objects.get_or_create(
            name="Комплексный сбор данных оборудования",
            defaults={
                "task": cls.name,
                "crontab": crontab,
                "enabled": False,
            },
        )

    def finish(self):
        """
        Очищает кэш для фильтров в панели администратора.
        """
        cache.delete("admin_device_filter_lookups")
        cache.delete("admin_vlan_filter_lookups")
        cache.delete("admin_type_filter_lookups")
        cache.delete("admin_port_filter_lookups")


mac_table_gather_task = app.register_task(MacTablesGatherTask())
configuration_gather_task = app.register_task(ConfigurationGatherTask())
vlan_table_gather_task = app.register_task(VlanTablesGatherTask())
devices_complex_gather_task = app.register_task(DevicesComplexGatherTask())


def get_mac_gather_status() -> dict:
    """
    Проверяет статус задачи `mac_table_gather_task`.

    :return: Словарь со статусом задачи.
    """

    task_id = cache.get("mac_table_gather_task_id")
    if task_id:
        task: AsyncResult = AsyncResult(str(task_id))
        if task.status == "PENDING":
            return {"status": "PENDING"}
        if task.status == "PROGRESS":
            return {"status": "PROGRESS", "progress": task.result.get("progress", "~")}

        cache.delete("mac_table_gather_task_id")

    return {
        "status": None,
        "progress": None,
    }


def get_vlan_gather_status() -> dict:
    """
    Проверяет статус задачи `vlan_table_gather_task`.

    :return: Словарь со статусом задачи.
    """

    task_id = cache.get("vlan_table_gather_task_id")
    if task_id:
        task: AsyncResult = AsyncResult(str(task_id))
        if task.status == "PENDING":
            return {"status": "PENDING"}
        if task.status == "PROGRESS":
            return {"status": "PROGRESS", "progress": task.result.get("progress", "~")}

        cache.delete("vlan_table_gather_task_id")

    return {
        "status": None,
        "progress": None,
    }
