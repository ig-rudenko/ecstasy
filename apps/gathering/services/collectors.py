from abc import ABC, abstractmethod
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import cache

import orjson
from celery import Task
from django.db import close_old_connections, connections
from django.db.models import QuerySet
from django.utils import timezone

from apps.check.models import Devices
from devicemanager.device import Interfaces
from devicemanager.vendors import BaseDevice

from ..models import DeviceGatheringResult, GatheringTask


class AbstractRealtimeCollector(ABC):
    """
    # This class is used for collecting realtime information from the device
    """

    def __init__(
        self,
        device: Devices,
        session: BaseDevice,
        interfaces: Interfaces,
        interfaces_desc: dict[str, str] | None = None,
        normalize_interface: Callable[[str], str] | None = None,
    ) -> None:
        self.device: Devices = device
        self.interfaces: Interfaces = interfaces or Interfaces()
        self.interfaces_desc: dict[str, str] = interfaces_desc or {}
        self.session = session
        self.normalize_interface = (
            cache(normalize_interface)
            if normalize_interface
            else cache(
                lambda i: self.session.normalize_interface_name(
                    self.session.normalize_interface_name_realtime(i)
                )
            )
        )

    def run_gathering(self) -> None:
        """Собрать и сохранить данные, передав ошибку вызывающей задаче."""

        if not self.interfaces_desc:
            # Нормализация имени интерфейса необходима из-за разных вариантов записи одного и того же порта.
            # Например - `1/1` и `1`, `26(C)` и `26(F)`.
            self.interfaces_desc = self.format_interfaces(self.interfaces)

        self.collect()

    @abstractmethod
    def collect(self) -> None:
        pass

    def format_interfaces(self, old_interfaces: Interfaces) -> dict:
        """
        ## Принимает список интерфейсов, и формирует словарь из интерфейсов и их описаний

        :return: Словарь интерфейсов и соответствующих им описаний.
        """
        interfaces = {}

        # Перебираем список интерфейсов
        for line in old_interfaces:
            normal_interface = self.normalize_interface(line.name)

            # Проверка, не является ли имя интерфейса пустым.
            if normal_interface:
                # Добавление имени интерфейса в качестве ключа и описания в качестве значения в словарь.
                interfaces[normal_interface] = line.desc

        return interfaces


class ThreadUpdatedStatusDeviceTask(Task):
    """
    Создает пул потоков, а затем отправляет задачу в пул потоков для каждого оборудования в наборе запросов.
    """

    queryset: QuerySet[Devices]
    max_workers: int

    def __init__(self):
        """
        Если набор запросов не определен, возникает ошибка
        """
        if not hasattr(self, "queryset"):
            raise NotImplementedError("Укажите queryset для работы данного класса")
        if not hasattr(self, "max_workers"):
            raise NotImplementedError("Укажите max_workers для работы данного класса")
        self.objects_count = 1
        self.objects_scanned = 0
        self.task_id = None

    def pre_run(self):
        """
        Вызывается перед началом симуляции
        """

    def run(self, *args, **kwargs):
        """
        Создает пул потоков, а затем отправляет задачу в пул потоков для каждого объекта в наборе запросов.

        :return: Возвращаемое значение является результатом метода return_value().
        """
        self.task_id = str(self.request.id)
        self.objects_count = self.queryset.count()
        self.objects_scanned = 0
        gathering_task = GatheringTask.objects.create(
            task_id=self.task_id,
            name=self.name,
            status=GatheringTask.Status.RUNNING,
            total_devices=self.objects_count,
        )

        try:
            self.pre_run()
            self.create_threads(gathering_task)
            self.finish()

            has_incomplete_results = gathering_task.device_results.exclude(
                status=DeviceGatheringResult.Status.SUCCESS
            ).exists()
            gathering_task.status = (
                GatheringTask.Status.PARTIAL if has_incomplete_results else GatheringTask.Status.SUCCESS
            )
        except Exception as error:
            gathering_task.status = GatheringTask.Status.FAILURE
            gathering_task.error_type = type(error).__name__[:128]
            gathering_task.error_message = self.error_message(error)
            raise
        finally:
            gathering_task.finished_at = timezone.now()
            gathering_task.save(update_fields=["status", "error_type", "error_message", "finished_at"])

        return self.return_value()

    def create_threads(self, gathering_task: GatheringTask):
        """
        Создает исполнителя пула потоков и отправляет ему задачу.
        """
        with ThreadPoolExecutor(max_workers=self.max_workers) as execute:
            futures = [
                execute.submit(self._run_thread_task, obj, gathering_task) for obj in self.queryset.all()
            ]
            for future in as_completed(futures):
                future.result()
                self.update_state()

    def _run_thread_task(self, obj: Devices, gathering_task: GatheringTask):
        """Run a worker task with a clean Django DB connection lifecycle."""
        close_old_connections()
        try:
            result = DeviceGatheringResult.objects.create(
                task=gathering_task,
                device=obj,
                status=DeviceGatheringResult.Status.RUNNING,
            )
            try:
                status = self.thread_task(obj) or DeviceGatheringResult.Status.SUCCESS
                result.status = status
                if status == DeviceGatheringResult.Status.SKIPPED:
                    result.error_type = "Unavailable"
            except Exception as error:
                result.status = DeviceGatheringResult.Status.FAILURE
                result.error_type = type(error).__name__[:128]
                result.error_message = self.error_message(error)
                self.log_error(device=obj, message=result.error_message)
            finally:
                result.finished_at = timezone.now()
                result.save(update_fields=["status", "error_type", "error_message", "finished_at"])

            return result.status
        finally:
            connections.close_all()

    def thread_task(self, obj: Devices, **kwargs):
        """
        Основная задача, которую необходимо выполнить для каждого объекта из queryset
        """
        raise NotImplementedError("Укажите задачу, которая должна выполняться")

    def return_value(self):
        """
        Что необходимо вернуть после выполнения всех потоков
        """
        return self.objects_count

    def update_state(self, task_id=None, state=None, meta=None, **kwargs):
        """
        Обновляет состояние задачи, а также обновляет ход выполнения задачи.

        :param task_id: Идентификатор задачи для обновления
        :param state: Состояние задачи
        :param meta: Это словарь, который содержит ход выполнения задачи
        """
        self.objects_scanned += 1
        super().update_state(
            task_id=task_id or self.task_id,
            state=state or "PROGRESS",
            meta=meta or {"progress": int(self.objects_scanned / self.objects_count * 100)},
            **kwargs,
        )

    @classmethod
    def register_task(cls):
        pass

    def finish(self):
        """Выполняется в самом конце после завершения задачи"""

    @staticmethod
    def error_message(error: Exception) -> str:
        """Вернуть ограниченное текстовое описание исключения."""

        return str(getattr(error, "message", error))[:2000]

    @staticmethod
    def device_log_format(device):
        return {"name": device.name, "ip": device.ip}

    def log(self, device: Devices, **kwargs):
        kwargs["message"] = str(kwargs.get("message", ""))

        data = {
            "task_id": self.task_id,
            "task_name": self.name,
            "task_args": self.request.args,
            "objects_count": self.objects_count,
            "objects_scanned": self.objects_scanned,
            "severity": kwargs.get("severity", "INFO"),
            **self.device_log_format(device),
            **kwargs,
        }
        print(orjson.dumps(data).decode("utf-8"), flush=True)

    def log_error(self, device: Devices, **kwargs):
        self.log(device, **kwargs, severity="ERROR")
