import json
from django.db.models.signals import post_delete
from django.db import models
from django.dispatch import receiver


class TransportRing(models.Model):
    NORMAL = "NORMAL"
    ROTATED = "ROTATED"
    DEACTIVATED = "DEACTIVATED"

    _STATUS = (
        (NORMAL, "Штатное состояние"),
        (ROTATED, "Развернуто"),
        (DEACTIVATED, "Деактивировано"),
    )

    name = models.CharField(max_length=100, unique=True)
    head = models.ForeignKey(
        "RingDevs", related_name="head_node", on_delete=models.SET_NULL, null=True, blank=True
    )
    tail = models.ForeignKey(
        "RingDevs", related_name="tail_node", on_delete=models.SET_NULL, null=True, blank=True
    )
    vlans = models.TextField()
    status = models.CharField(choices=_STATUS, max_length=20, default=NORMAL)
    description = models.TextField()

    def __setattr__(self, key, value):
        if key == "vlans":
            # Принимаем список в качестве входных данных и преобразует его в строку JSON
            self._vlans = json.dumps(value)
        super().__setattr__(key, value)

    def __getattribute__(self, item):
        if item == "vlans":
            # Меняем поведение для vlans
            if isinstance(self.__dict__[item], list):
                return self.__dict__[item]

            # Преобразовываем в список, если это не было сделано ранее
            self.__dict__[item] = json.loads(self.__dict__[item])
            return self.__dict__[item]

        return super().__getattribute__(item)

    def __str__(self):
        return f"TransportRing: {self.name} head: {self.head.device.name}"


class RingDevs(models.Model):

    device = models.ForeignKey("check.Devices", on_delete=models.CASCADE, null=False)
    ring_name = models.CharField(max_length=100)
    next_dev = models.ForeignKey(
        "self", on_delete=models.SET_NULL, related_name="next_node", null=True, blank=True
    )
    prev_dev = models.ForeignKey(
        "self", on_delete=models.SET_NULL, related_name="prev_node", null=True, blank=True
    )

    def __str__(self):
        return f"TransportRing: {self.ring_name} Dev ({self.device}) prev: [{self.prev_dev}] | next: [{self.next_dev}]"


@receiver(post_delete, sender=RingDevs)
def normalize_ring_structure(sender, instance: RingDevs, *args, **kwargs):
    if instance.next_dev and instance.prev_dev:
        # Этот код проверяет, имеет ли удаленный экземпляр атрибуты next_dev и prev_dev, и если да,
        # обновляет атрибут next_dev экземпляра prev_dev, чтобы он указывал на экземпляр next_dev удаленного экземпляра.
        # Это позволяет удалить экземпляр из кольцевой структуры, не разорвав кольцо.
        instance.prev_dev.next_dev = instance.next_dev.prev_dev
