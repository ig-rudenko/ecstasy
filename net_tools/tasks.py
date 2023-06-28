from celery.result import AsyncResult
from django.core.cache import cache

from ecstasy_project.celery import app
from ecstasy_project.task import ThreadUpdatedStatusTask
from check.interfaces_collector import DeviceInterfacesCollectorMixin
from check.models import Devices as ModelDevices
from devicemanager.device import DeviceManager


class InterfacesScanTask(ThreadUpdatedStatusTask):
    name = "interfaces_scan"
    queryset = ModelDevices.objects.all()

    def pre_run(self):
        super().pre_run()
        cache.set("periodically_scan_id", self.request.id, timeout=None)

    def thread_task(self, obj: ModelDevices, **kwargs):
        if not obj.available:
            # Если оборудование недоступно, то пропускаем
            return

        collector = DeviceInterfacesCollectorMixin()
        collector.device = obj
        collector.device_collector = DeviceManager.from_model(obj)
        collector.collect_current_interfaces()
        collector.sync_device_info_to_db()
        collector.device_collector.push_zabbix_inventory()
        collector.save_interfaces_to_db()
        print(f"Saved Interfaces --> {obj}")

        self.update_state()


interfaces_scan = app.register_task(InterfacesScanTask())


def check_scanning_status() -> dict:
    task_id = cache.get("periodically_scan_id")
    if task_id:
        task = AsyncResult(str(task_id))
        if task.status == "PENDING":
            return {"status": "PENDING"}
        if task.status == "PROGRESS":
            return {"status": "PROGRESS", "progress": task.result.get("progress", "~")}

        cache.delete("periodically_scan_id")

    return {
        "status": None,
    }
