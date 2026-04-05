from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from time import monotonic

from celery import shared_task
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from devicemanager.remote.exceptions import InvalidMethod

from .models import (
    BulkDeviceCommandExecution,
    BulkDeviceCommandExecutionResult,
    DeviceCommand,
    Devices,
    UsersActions,
)
from .services.device.commands import (
    execute_command,
    get_command_text_for_audit,
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


def _update_execution_progress(task_id: str, processed: int, total: int) -> None:
    """Persist execution progress for audit history."""
    BulkDeviceCommandExecution.objects.filter(task_id=task_id).update(
        status=BulkDeviceCommandExecution.STATUS_PROGRESS,
        processed=processed,
        total=total,
        progress=int(processed / max(total, 1) * 100),
    )


def _save_execution_result(
    task_id: str,
    device: Devices,
    status: str,
    command_text: str,
    output: str,
    detail: str,
    error: str,
    duration: float,
) -> None:
    """Persist one device result for bulk command audit."""
    execution = BulkDeviceCommandExecution.objects.filter(task_id=task_id).first()
    if execution is None:
        return

    BulkDeviceCommandExecutionResult.objects.update_or_create(
        execution=execution,
        device=device,
        defaults={
            "device_name": device.name,
            "status": status,
            "command_text": command_text,
            "output": output,
            "detail": detail,
            "error": error,
            "duration": round(duration, 3),
        },
    )


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
            _update_execution_progress(task_id, processed, len(devices))
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
        command_text = ""

        if not is_command_available_for_device(command, device):
            result = _build_bulk_command_result(
                device=device,
                status="SKIPPED",
                detail="Command is unavailable for this device",
            )
            _save_execution_result(
                task_id=task_id,
                device=device,
                status=BulkDeviceCommandExecutionResult.STATUS_SKIPPED,
                command_text="",
                output="",
                detail="Command is unavailable for this device",
                error="",
                duration=monotonic() - started_at,
            )
            update_progress()
            return result

        try:
            command_text = get_command_text_for_audit(device, command, context)
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
            _save_execution_result(
                task_id=task_id,
                device=device,
                status=BulkDeviceCommandExecutionResult.STATUS_ERROR,
                command_text=command_text,
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
            _save_execution_result(
                task_id=task_id,
                device=device,
                status=BulkDeviceCommandExecutionResult.STATUS_ERROR,
                command_text=command_text,
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
            _save_execution_result(
                task_id=task_id,
                device=device,
                status=BulkDeviceCommandExecutionResult.STATUS_SUCCESS,
                command_text=command_text,
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

    final_status = BulkDeviceCommandExecution.STATUS_SUCCESS
    if BulkDeviceCommandExecutionResult.objects.filter(
        execution__task_id=task_id,
        status=BulkDeviceCommandExecutionResult.STATUS_ERROR,
    ).exists():
        final_status = BulkDeviceCommandExecution.STATUS_FAILURE

    BulkDeviceCommandExecution.objects.filter(task_id=task_id).update(
        status=final_status,
        processed=processed,
        total=len(devices),
        progress=100 if devices else 0,
        finished_at=timezone.now(),
    )

    return {
        "taskId": task_id,
        "total": len(devices),
        "processed": processed,
    }
