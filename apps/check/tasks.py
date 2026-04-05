from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from time import monotonic

from celery import shared_task
from rest_framework.exceptions import ValidationError

from devicemanager.remote.exceptions import InvalidMethod

from .models import DeviceCommand, Devices, UsersActions
from .services.device.commands import (
    execute_command,
    init_device_command_task_results_cache,
    is_command_available_for_device,
    update_device_command_task_result,
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


def _build_bulk_command_cache_result(
    device: Devices,
    command: DeviceCommand,
    status: str,
    output: str,
    detail: str,
    error: str,
    duration: float,
) -> dict:
    """Build cached execution payload for a single device."""
    return {
        "device_id": device.id,
        "device_name": device.name,
        "status": status,
        "command_id": command.id,
        "command_text": command.command,
        "output": output,
        "detail": detail,
        "error": error,
        "duration": round(duration, 3),
    }


def _get_bulk_command_workers_count(devices_count: int) -> int:
    """Return worker count for bulk command execution."""
    return max(1, min(devices_count, 32))


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
    init_device_command_task_results_cache(task_id)

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
        started_at = monotonic()

        if not is_command_available_for_device(command, device):
            result = _build_bulk_command_result(
                device=device,
                status="SKIPPED",
                detail="Command is unavailable for this device",
            )
            update_progress()
            return result

        try:
            output = execute_command(device, command, context)
        except (InvalidMethod, ValidationError) as exc:
            result = _build_bulk_command_result(device=device, status="ERROR", detail=str(exc))
            cache_result = _build_bulk_command_cache_result(
                device=device,
                command=command,
                status="ERROR",
                output="",
                detail=str(exc),
                error=str(exc),
                duration=monotonic() - started_at,
            )
        except Exception as exc:
            result = _build_bulk_command_result(device=device, status="ERROR", detail=str(exc))
            cache_result = _build_bulk_command_cache_result(
                device=device,
                command=command,
                status="ERROR",
                output="",
                detail=str(exc),
                error=str(exc),
                duration=monotonic() - started_at,
            )
        else:
            result = _build_bulk_command_result(device=device, status="SUCCESS", output=output)
            cache_result = _build_bulk_command_cache_result(
                device=device,
                command=command,
                status="SUCCESS",
                output=output,
                detail="",
                error="",
                duration=monotonic() - started_at,
            )
            UsersActions.objects.create(
                user_id=user_id,
                device=device,
                action=f"execute bulk command {command.name}",
            )

        update_device_command_task_result(task_id, device.id, cache_result)
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
