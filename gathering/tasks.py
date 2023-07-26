import logging

import pexpect.exceptions
from celery.result import AsyncResult
from django.core.cache import cache
from pyzabbix.api import logger

from ecstasy_project.task import ThreadUpdatedStatusTask
from ecstasy_project.celery import app
from check.models import Devices
from .mac import MacAddressTableGather
from .configurations.collector import ConfigurationGather
from .configurations.exceptions import ConfigFileError
from .configurations.local_storage import LocalConfigStorage


class MacTablesGatherTask(ThreadUpdatedStatusTask):
    """
    # Celery задача для сбора таблицы MAC адресов оборудования.

    Использует пул потоков, а затем отправляет задачу на сбор MAC для каждого оборудования в queryset.

    Задача обновляет свой статус после каждого завершенного сбора на оборудовании.
    """

    name = "mac_table_gather_task"
    queryset = Devices.objects.all()
    max_workers = 80

    def pre_run(self):
        """
        Он устанавливает ключ кэша с именем «mac_table_gather_task_id» на идентификатор текущей задачи.
        """
        super().pre_run()
        logger.setLevel(logging.ERROR)
        cache.set("mac_table_gather_task_id", self.request.id, timeout=None)

    def thread_task(self, obj: Devices, **kwargs):
        try:
            if not obj.available:
                return
            gather = MacAddressTableGather(obj)
            gather.clear_old_records()
            print(f"{obj} bulk_create: {gather.bulk_create()}")
        except pexpect.exceptions.ExceptionPexpect as error:
            print(f"{obj} --> {error}")
        finally:
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
        storage = LocalConfigStorage(obj)
        try:
            gather = ConfigurationGather(storage=storage)
            gather.delete_outdated_configs()
            status = gather.collect_config_file()
            print(f"configuration_gather_task {status} {obj}")
        except ConfigFileError as error:
            print(f"configuration_gather_task {error.message} {obj}")

        self.update_state()


# Регистрация задачи в приложении Celery.
configuration_gather_task = app.register_task(ConfigurationGatherTask())
