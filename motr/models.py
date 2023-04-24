from django.db import models


class Ring(models.Model):
    name = models.CharField(max_length=100, unique=True)
    head = models.ForeignKey(
        "RingDevs", related_name="head_node", on_delete=models.SET_NULL, null=True, blank=True
    )
    tail = models.ForeignKey(
        "RingDevs", related_name="tail_node", on_delete=models.SET_NULL, null=True, blank=True
    )
    vlans = models.TextField()

    def __str__(self):
        return f"Ring: {self.name} head: {self.head.device.name}"


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
        return f"Ring: {self.ring_name} Dev ({self.device}) prev: [{self.prev_dev}] | next: [{self.next_dev}]"
