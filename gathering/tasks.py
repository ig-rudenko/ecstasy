from celery.result import AsyncResult
from django.core.cache import cache

from ecstasy_project.task import ThreadUpdatedStatusTask
from ecstasy_project.celery import app
from check.models import Devices
from .collectors import MacAddressTableGather, ConfigurationGather


class MacTablesGatherTask(ThreadUpdatedStatusTask):
    """
    # Celery задача для сбора таблицы MAC адресов оборудования.

    Использует пул потоков, а затем отправляет задачу на сбор MAC для каждого оборудования в queryset.

    Задача обновляет свой статус после каждого завершенного сбора на оборудовании.
    """

    name = "mac_table_gather_task"
    queryset = Devices.objects.all()

    def pre_run(self):
        """
        Он устанавливает ключ кэша с именем «mac_table_gather_task_id» на идентификатор текущей задачи.
        """
        super().pre_run()
        cache.set("mac_table_gather_task_id", self.request.id, timeout=None)

    def thread_task(self, obj: Devices, **kwargs):
        gather = MacAddressTableGather(obj)
        gather.clear_old_records()
        print(f"{obj} bulk_create: {gather.bulk_create()}")
        self.update_state()


# Регистрация задачи в приложении Celery.
mac_table_gather_task = app.register_task(MacTablesGatherTask())


def check_scanning_status() -> dict:
    """
    Проверяет статус задачи `mac_table_gather_task`.

    :return: Словарь со статусом задачи.
    """

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


class ConfigurationGatherTask(ThreadUpdatedStatusTask):
    """
    # Celery задача для сбора таблицы MAC адресов оборудования.

    Использует пул потоков, а затем отправляет задачу на сбор MAC для каждого оборудования в queryset.

    Задача обновляет свой статус после каждого завершенного сбора на оборудовании.
    """

    name = "configuration_gather_task"
    queryset = Devices.objects.all()

    def thread_task(self, obj: Devices, **kwargs):
        gather = ConfigurationGather(obj)
        gather.delete_outdated_configs()
        gather.collect_config_file()
        self.update_state()


# Регистрация задачи в приложении Celery.
configuration_gather_task = app.register_task(ConfigurationGatherTask())
