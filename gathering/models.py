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
