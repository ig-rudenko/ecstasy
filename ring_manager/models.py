import json

from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver


class TransportRing(models.Model):
    NORMAL = "NORMAL"
    DEACTIVATED = "DEACTIVATED"  # Кольцо отключено
    IN_PROCESS = "IN_PROCESS"  # Совершается какое-то действие с кольцом

    _STATUS = (
        (NORMAL, "Штатное состояние"),
        (DEACTIVATED, "Деактивировано"),
        (IN_PROCESS, "Занято в данный момент"),
    )

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Название кольца",
        help_text="Это название будет отображаться в меню колец",
    )
    description = models.TextField(verbose_name="Описание")
    users = models.ManyToManyField(
        "auth.User",
        verbose_name="Пользователи",
        help_text="Выберите, кто будет иметь доступ к кольцу",
    )

    head = models.ForeignKey(
        "ring_manager.RingDev",
        related_name="head_node",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Головное устройство",
        help_text="Необходимо для начала создать головную точку, а затем выбрать её. "
        "Данная точка будет ведущей в кольце.",
    )
    tail = models.ForeignKey(
        "ring_manager.RingDev",
        related_name="tail_node",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Оконечная точка в кольце.",
        help_text="Для данного оборудования будут добавляться VLAN в случае разворота кольца",
    )
    # Форматируется при обращении в list
    vlans: list = models.TextField(
        verbose_name="VLAN'S",
        help_text="Укажите через запятую, "
        "какие VLAN необходимо добавить для оконечного оборудования в кольце в случае разворота",
    )  # type: ignore
    status = models.CharField(
        choices=_STATUS,
        max_length=20,
        default=NORMAL,
        verbose_name="Состояние кольца",
        help_text="Какое в данный момент состояние имеет кольцо",
    )
    solution_time = models.DateTimeField(null=True, blank=True)
    solutions = models.JSONField(null=True, blank=True, default=list)

    def __setattr__(self, key, value):
        """
        Эта функция переопределяет метод setattr по умолчанию и преобразует ввод списка в строку JSON
        для атрибута «vlans»

        :param key: Имя устанавливаемого атрибута
        :param value: Значение, которое присваивается атрибуту/ключу в объекте
        """
        if key == "vlans":
            # Принимаем список в качестве входных данных и преобразует его в строку JSON
            self._vlans = json.dumps(value)
        super().__setattr__(key, value)

    def __getattribute__(self, item: str):
        """
        Эта функция переопределяет поведение по умолчанию при доступе к атрибуту объекта и преобразует
        атрибут "vlans" из строки JSON в список целых чисел.

        :param item: Строка, представляющая имя атрибута, к которому осуществляется доступ в классе.
         В этом случае код проверяет, является ли запрашиваемый атрибут «vlans»
        :return: Если элементом является «vlans», метод возвращает либо существующий список vlan, либо новый список
         vlan, созданный путем синтаксического анализа строки JSON. Если элемент не является «vlans», метод возвращает
         атрибут, используя поведение родительского класса по умолчанию.
        """

        if item == "vlans":
            # Меняем поведение для vlans
            if isinstance(self.__dict__[item], list):
                return self.__dict__[item]

            # Этот блок кода отвечает за преобразование атрибута vlans из строки JSON в список целых чисел.
            origin: str = self.__dict__[item].replace("[", "").replace("]", "")
            origin = f"[{origin}]"
            self.__dict__[item] = json.loads(origin)
            return self.__dict__[item]

        return super().__getattribute__(item)

    def __str__(self):
        head = self.head.device.name if self.head else None
        tail = self.tail.device.name if self.tail else None
        return f"TransportRing: {self.name} head: {head}, tail: {tail}"

    def set_status_in_progress(self):
        """
        Эта функция устанавливает статус кольца в «in progress», для того, чтобы применить решения.
        """
        self.status = self.IN_PROCESS
        self.save(update_fields=["status"])

    def set_status_normal(self, clear_solutions: bool):
        """
        Эта функция устанавливает нормальный статус кольца и опционально очищает его предыдущие решения.

        :param clear_solutions: clear_solutions — это логический параметр, определяющий, следует ли очищать поле решений
         объекта.
        """
        self.status = self.NORMAL
        update_fields = ["status"]
        if clear_solutions:
            self.solutions = None
            update_fields.append("solutions")

        self.save(update_fields=update_fields)

    def set_status_deactivated(self):
        """
        Эта функция устанавливает статус объекта на «deactivated», это означает, что кольцо не будет использоваться
        """
        self.status = self.DEACTIVATED
        self.save(update_fields=["status"])


class RingDev(models.Model):
    device = models.ForeignKey(
        "check.Devices",
        on_delete=models.CASCADE,
        null=False,
        verbose_name="Оборудование",
        help_text="Выберите устройство, которое находится в кольце",
    )
    ring_name = models.CharField(
        max_length=100,
        verbose_name="Названия кольца, где будет данное устройство",
    )
    next_dev = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="next_node",
        null=True,
        blank=True,
        verbose_name="Следующее устройство",
        help_text="Начиная от головного устройства укажите следующее за данным",
    )
    prev_dev = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="prev_node",
        null=True,
        blank=True,
        verbose_name="Предыдущее устройство",
    )

    def __str__(self):
        return f"TransportRing: {self.ring_name} Dev: ({self.device})"


@receiver(post_delete, sender=RingDev)
def normalize_ring_structure(sender, instance: RingDev, *args, **kwargs):
    if instance.next_dev and instance.prev_dev:
        # Этот код проверяет, имеет ли удаленный экземпляр атрибуты next_dev и prev_dev, и если да,
        # обновляет атрибут next_dev экземпляра prev_dev, чтобы он указывал на экземпляр next_dev удаленного экземпляра.
        # Это позволяет удалить экземпляр из кольцевой структуры, не разорвав кольцо.
        instance.prev_dev.next_dev = instance.next_dev.prev_dev
