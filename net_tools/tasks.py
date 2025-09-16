import logging

from celery.result import AsyncResult
from django.core.cache import cache
from django_celery_beat.models import CrontabSchedule, PeriodicTask
from pyzabbix.api import logger

from check.models import Devices as ModelDevices
from check.services.device.interfaces_collector import DeviceDBSynchronizer
from devicemanager.device import DeviceManager
from ecstasy_project.celery import app
from ecstasy_project.task import ThreadUpdatedStatusTask


class InterfacesScanTask(ThreadUpdatedStatusTask):
    max_workers = 80
    name = "interfaces_scan"
    queryset = ModelDevices.objects.filter(active=True, collect_interfaces=True)

    def pre_run(self):
        super().pre_run()
        logger.setLevel(logging.ERROR)
        cache.set("periodically_scan_id", self.request.id, timeout=None)

    def thread_task(self, obj: ModelDevices, **kwargs):
        if not obj.available:
            # Если оборудование недоступно, то пропускаем
            return

        try:
            synchronizer = DeviceDBSynchronizer(
                device=obj,
                device_collector=DeviceManager.from_model(obj),
                with_vlans=True,
            )

            synchronizer.collect_current_interfaces(make_session_global=False)
            synchronizer.sync_device_info_to_db()
            synchronizer.device_collector.push_zabbix_inventory()
            synchronizer.save_interfaces_to_db()
            self.log(device=self.device_log_format(obj), message="Интерфейсы успешно обновлены")
        except Exception as exc:
            self.log_error(device=self.device_log_format(obj), message=exc)

        self.update_state()

    @classmethod
    def register_task(cls):
        crontab, _ = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="*/2",
        )
        PeriodicTask.objects.get_or_create(
            name="Опрос интерфейсов оборудования",
            task=cls.name,
            crontab=crontab,
        )


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
