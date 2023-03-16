from celery.result import AsyncResult
from django.core.cache import cache

from ecstasy_project.task import ThreadUpdatedStatusTask
from ecstasy_project.celery import app
from check.models import Devices
from .collectors import GatherMacAddressTable


class MacTablesGatherTask(ThreadUpdatedStatusTask):
    name = "mac_table_gather_task"
    queryset = Devices.objects.all()

    def pre_run(self):
        super().pre_run()
        cache.set("mac_table_gather_task_id", self.request.id, timeout=None)

    def thread_task(self, obj: Devices, **kwargs):
        gather = GatherMacAddressTable(obj)
        gather.clear_old_records()
        gather.bulk_create()
        self.update_state()


mac_table_gather_task = app.register_task(MacTablesGatherTask())


def check_scanning_status() -> dict:
    task_id = cache.get("mac_table_gather_task_id")
    if task_id:
        task = AsyncResult(str(task_id))
        if task.status == "PENDING":
            return {"status": "PENDING"}
        if task.status == "PROGRESS":
            return {"status": "PROGRESS", "progress": task.result.get("progress", "~")}

        cache.delete("mac_table_gather_task_id")

    return {
        "status": None,
    }
