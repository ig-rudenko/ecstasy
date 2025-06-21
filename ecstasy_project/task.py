from concurrent.futures import ThreadPoolExecutor

from celery import Task
from django.db.models import QuerySet  # noqa: F401

from app_settings.models import ZabbixConfig
from devicemanager.device import zabbix_api


class ThreadUpdatedStatusTask(Task):
    """
    # Создает пул потоков, а затем отправляет задачу в пул потоков для каждого объекта в наборе запросов.
    """

    queryset = None  # type: QuerySet
    max_workers = None  # type: int

    def __init__(self):
        """
        ## Если набор запросов не определен, возникает ошибка
        """
        if self.queryset is None:
            raise NotImplementedError("Укажите queryset для работы данного класса")
        self.objects_count = 1
        self.objects_scanned = 0
        self.task_id = None

    def pre_run(self):
        """
        ## Эта функция вызывается перед началом симуляции
        """
        zabbix_api.set_lazy_attributes(ZabbixConfig.load())

    def run(self, *args, **kwargs):
        """
        ## Он создает пул потоков, а затем отправляет задачу в пул потоков для каждого объекта в наборе запросов.
        :return: Возвращаемое значение является результатом метода return_value().
        """
        self.pre_run()

        self.task_id = self.request.id
        self.objects_count = self.queryset.count()
        self.objects_scanned = 0

        self.create_threads()

        return self.return_value()

    def create_threads(self):
        """
        Он создает исполнителя пула потоков и отправляет ему задачу.
        """
        with ThreadPoolExecutor(max_workers=self.max_workers) as execute:
            for obj in self.queryset.all():
                execute.submit(self.__class__.thread_task, self, obj)

    def thread_task(self, obj, **kwargs):
        """
        Основная задача, которую необходимо выполнить для каждого объекта из queryset
        :param obj: Объект из queryset
        """
        raise NotImplementedError("Укажите задачу, которая должна выполняться")

    def return_value(self):
        """
        Что необходимо вернуть после выполнения всех потоков
        """
        return self.objects_count

    def update_state(self, task_id=None, state=None, meta=None, **kwargs):
        """
        Он обновляет состояние задачи, а также обновляет ход выполнения задачи.

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
