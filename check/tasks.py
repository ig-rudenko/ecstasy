from celery import shared_task

from check.services.device.interfaces_workload import DevicesInterfacesWorkloadCollector


@shared_task(ignore_result=True)
def cache_all_devices_interfaces_workload_api_view():
    collector = DevicesInterfacesWorkloadCollector()
    # Обновляем кэш
    collector.get_all_device_interfaces_workload(from_cache=False)
