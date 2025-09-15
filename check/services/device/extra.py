from check.models import Devices
from ecstasy_project.decorators import cached


@cached(60, key="device_names_list")
def get_all_device_names_list() -> list[str]:
    return list(Devices.objects.all().values_list("name", flat=True))


@cached(60, key=lambda device: f"device_stats:{device.name}")
def get_device_stats(device: Devices) -> dict:
    return device.connect().get_device_info()
