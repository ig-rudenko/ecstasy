from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class MacAddress(models.Model):
    address = models.CharField(max_length=12)
    vlan = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(4096),
        ]
    )
    type = models.CharField(max_length=1)
    device = models.ForeignKey("check.Devices", on_delete=models.CASCADE)
    port = models.CharField(max_length=50)
    desc = models.CharField(max_length=128)
    datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "mac_addresses"
        unique_together = ("address", "device", "port")
        indexes = [
            models.Index(fields=("address",), name="mac_address_index"),
        ]
class Vlan(models.Model):
    vlan = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4096)]
    )
    vlan_desc = models.CharField(max_length=50)
    device = models.ForeignKey("check.Devices", on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now=True)  # Обновляется при каждом сохранении

    class Meta:
        db_table = "vlan"
        unique_together = ("vlan", "device")  # Уникальность по двум полям
        indexes = [models.Index(fields=("vlan",), name="vlan_index")]

    def __str__(self):
        return f"VLAN {self.vlan} - {self.vlan_desc}"

class VlanPort(models.Model):
    vlan = models.ForeignKey(Vlan, related_name="ports", on_delete=models.CASCADE)
    port = models.CharField(max_length=50)
    desc_port = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        db_table = "vlan_port"
        unique_together = ("vlan", "port")

    def __str__(self):
        return f"{self.port}"
