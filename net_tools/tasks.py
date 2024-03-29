import logging
from typing import cast

from celery.result import AsyncResult
from django.core.cache import cache
from pyzabbix.api import logger

from check.interfaces_collector import DeviceInterfacesCollectorMixin
from check.models import Devices as ModelDevices, Devices
from devicemanager.device import DeviceManager
from ecstasy_project.celery import app
from ecstasy_project.task import ThreadUpdatedStatusTask


class DeviceInterfacesCollector(DeviceInterfacesCollectorMixin):
    @property
    def device(self) -> Devices:
        return cast(Devices, self._device)

    @device.setter
    def device(self, device: Devices) -> None:
        self._device = device

    @property
    def device_collector(self) -> DeviceManager:
        return cast(DeviceManager, self._device_collector)

    @device_collector.setter
    def device_collector(self, device_collector: DeviceManager) -> None:
        self._device_collector = device_collector


class InterfacesScanTask(ThreadUpdatedStatusTask):
    max_workers = 80
    name = "interfaces_scan"
    queryset = ModelDevices.objects.all()

    def pre_run(self):
        super().pre_run()
        logger.setLevel(logging.ERROR)
        cache.set("periodically_scan_id", self.request.id, timeout=None)

    def thread_task(self, obj: ModelDevices, **kwargs):
        if not obj.available:
            # Если оборудование недоступно, то пропускаем
            return

        try:
            print(f"Start collect interfaces --> {obj}")
            collector = DeviceInterfacesCollector()
            collector.with_vlans = True
            collector.device = obj
            collector.device_collector = DeviceManager.from_model(obj)
            collector.collect_current_interfaces(make_session_global=False)
            collector.sync_device_info_to_db()
            collector.device_collector.push_zabbix_inventory()
            collector.save_interfaces_to_db()
            print(f"Saved Interfaces --> {obj}")
        except Exception as e:
            print(f"Error when collect interfaces of {obj}: {e}")

        self.update_state()


interfaces_scan = app.register_task(InterfacesScanTask())


def check_scanning_status() -> dict:
    task_id = cache.get("periodically_scan_id")
    if task_id:
        task: AsyncResult = AsyncResult(str(task_id))
        if task.status == "PENDING":
            return {"status": "PENDING"}
        if task.status == "PROGRESS":
            return {"status": "PROGRESS", "progress": task.result.get("progress", "~")}

        cache.delete("periodically_scan_id")

    return {
        "status": None,
    }
