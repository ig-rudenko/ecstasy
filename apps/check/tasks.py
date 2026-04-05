from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from celery import shared_task
from django.core.cache import cache
from rest_framework.exceptions import ValidationError

from devicemanager.remote.exceptions import InvalidMethod

from .models import DeviceCommand, Devices, UsersActions
from .services.device.commands import (
    execute_command,
    get_device_command_task_cache_key,
    is_command_available_for_device,
)
from .services.device.interfaces_workload import DevicesInterfacesWorkloadCollector


@shared_task(ignore_result=True)
def cache_all_devices_interfaces_workload_api_view():
    """Warm up cache with interfaces workload for all devices."""
    collector = DevicesInterfacesWorkloadCollector(Devices.objects.all())
    collector.get_all_device_interfaces_workload(from_cache=False)


def _build_bulk_command_result(device: Devices, status: str, output: str = "", detail: str = "") -> dict:
    """Build cached execution result for a single device."""
    return {
        "deviceId": device.id,
        "deviceName": device.name,
        "status": status,
        "output": output,
        "detail": detail,
    }


def _get_bulk_command_workers_count(devices_count: int) -> int:
    """Return worker count for bulk command execution."""
    return max(1, min(devices_count, 32))


def _save_bulk_command_result(task_id: str, device: Devices, result: dict) -> None:
    """Save device command execution result to cache."""
    cache.set(get_device_command_task_cache_key(task_id, device.id), result, timeout=None)


@shared_task(bind=True, name="execute_bulk_device_command_task")
def execute_bulk_device_command_task(
    self, command_id: int, device_ids: list[int], context: dict, user_id: int
) -> dict:
    """Execute one command on multiple devices in parallel."""
    devices = list(Devices.objects.filter(id__in=device_ids).select_related("auth_group"))
    command = DeviceCommand.objects.get(id=command_id)
    task_id = str(self.request.id)
    total = max(len(devices), 1)
    processed = 0
    progress_lock = Lock()

    def update_progress() -> None:
        """Update celery progress state."""
        nonlocal processed
        with progress_lock:
            processed += 1
            self.update_state(
                state="PROGRESS",
                meta={
                    "progress": int(processed / total * 100),
                    "processed": processed,
                    "total": len(devices),
                },
            )

    def run_for_device(device: Devices) -> dict:
        """Run the command for a single device and cache the result."""
        if not is_command_available_for_device(command, device):
            result = _build_bulk_command_result(
                device=device,
                status="SKIPPED",
                detail="Command is unavailable for this device",
            )
            _save_bulk_command_result(task_id, device, result)
            update_progress()
            return result

        try:
            output = execute_command(device, command, context)
        except (InvalidMethod, ValidationError) as exc:
            result = _build_bulk_command_result(device=device, status="ERROR", detail=str(exc))
        except Exception as exc:
            result = _build_bulk_command_result(device=device, status="ERROR", detail=str(exc))
        else:
            result = _build_bulk_command_result(device=device, status="SUCCESS", output=output)
            UsersActions.objects.create(
                user_id=user_id,
                device=device,
                action=f"execute bulk command {command.name}",
            )

        _save_bulk_command_result(task_id, device, result)
        update_progress()
        return result

    with ThreadPoolExecutor(max_workers=_get_bulk_command_workers_count(len(devices))) as executor:
        futures = [executor.submit(run_for_device, device) for device in devices]
        for future in as_completed(futures):
            future.result()

    return {
        "taskId": task_id,
        "total": len(devices),
        "processed": processed,
    }
