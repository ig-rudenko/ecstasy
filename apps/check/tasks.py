import re
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from time import monotonic, sleep

from celery import shared_task
from django.db import close_old_connections, connection
from django.db.utils import OperationalError
from django.utils import timezone

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
    set_device_command_task_results,
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


def _mark_execution_started(task_id: str, total: int) -> None:
    """Mark bulk execution as started before first device result is received."""
    BulkDeviceCommandExecution.objects.filter(task_id=task_id).update(
        status=BulkDeviceCommandExecution.STATUS_PROGRESS,
        processed=0,
        total=total,
        progress=0,
    )


def _save_execution_result(
    execution_id: int,
    device: Devices,
    status: str,
    command_text: str,
    output: str,
    detail: str,
    error: str,
    duration: float,
) -> None:
    """Persist one device result for bulk command audit."""
    BulkDeviceCommandExecutionResult.objects.update_or_create(
        execution_id=execution_id,
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


def _is_sqlite_backend() -> bool:
    """Return True when current configured database backend is SQLite."""
    return connection.vendor == "sqlite"


def _save_execution_result_with_retry(
    execution_id: int,
    device: Devices,
    status: str,
    command_text: str,
    output: str,
    detail: str,
    error: str,
    duration: float,
) -> None:
    """Persist one device result and retry short SQLite lock conflicts."""
    attempts = 5 if _is_sqlite_backend() else 1
    for attempt in range(attempts):
        try:
            _save_execution_result(
                execution_id=execution_id,
                device=device,
                status=status,
                command_text=command_text,
                output=output,
                detail=detail,
                error=error,
                duration=duration,
            )
            return
        except OperationalError as exc:
            is_locked = "database is locked" in str(exc).lower()
            if not is_locked or attempt == attempts - 1:
                raise
            sleep(0.05 * (attempt + 1))


@shared_task(bind=True, name="execute_bulk_device_command_task")
def execute_bulk_device_command_task(
    self, command_id: int, device_ids: list[int], context: dict, user_id: int
) -> dict:
    """Execute one command on multiple devices in parallel."""
    devices = list(Devices.objects.filter(id__in=device_ids).select_related("auth_group"))
    command = DeviceCommand.objects.get(id=command_id)
    task_id = str(self.request.id)
    execution = BulkDeviceCommandExecution.objects.get(task_id=task_id)
    total = max(len(devices), 1)
    processed = 0
    progress_lock = Lock()
    results_lock = Lock()
    db_write_lock = Lock()
    cached_results: dict[str, dict] = {}
    init_device_command_task_results_cache(task_id)
    _mark_execution_started(task_id, len(devices))

    def sync_cache() -> None:
        """Persist current in-memory results snapshot to cache."""
        set_device_command_task_results(task_id, cached_results)

    def register_result(device: Devices, cache_result: dict) -> None:
        """Store one device result in the in-memory cache and persist snapshot."""
        with results_lock:
            cached_results[str(device.id)] = cache_result
            sync_cache()

    def update_progress() -> None:
        """Update persisted progress state."""
        nonlocal processed
        with progress_lock:
            processed += 1
            with db_write_lock:
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
        close_old_connections()
        started_at = monotonic()
        command_text = ""

        if not is_command_available_for_device(command, device):
            detail = "Command is unavailable for this device"
            cache_result = _build_bulk_command_cache_result(
                device=device,
                command=command,
                status="SKIPPED",
                output="",
                detail=detail,
                error="",
                duration=monotonic() - started_at,
            )
            with db_write_lock:
                _save_execution_result_with_retry(
                    execution_id=execution.id,
                    device=device,
                    status=BulkDeviceCommandExecutionResult.STATUS_SKIPPED,
                    command_text="",
                    output="",
                    detail=detail,
                    error="",
                    duration=monotonic() - started_at,
                )
            register_result(device, cache_result)
            return _build_bulk_command_result(device=device, status="SKIPPED", detail=detail)

        try:
            command_text = get_command_text_for_audit(device, command, context)
            output = execute_command(device, command, context)

            # Если есть проверка выполнения команды.
            if command.valid_regexp and not re.compile(command.valid_regexp).search(output):
                raise Exception(output)

        except Exception as exc:
            print(f"Task ID: {task_id} | Exception on device: {exc}")
            error_text = str(exc)
            cache_result = _build_bulk_command_cache_result(
                device=device,
                command=command,
                status="ERROR",
                output="",
                detail=error_text,
                error=error_text,
                duration=monotonic() - started_at,
            )
            with db_write_lock:
                _save_execution_result_with_retry(
                    execution_id=execution.id,
                    device=device,
                    status=BulkDeviceCommandExecutionResult.STATUS_ERROR,
                    command_text=command_text,
                    output="",
                    detail=error_text,
                    error=error_text,
                    duration=monotonic() - started_at,
                )
            register_result(device, cache_result)
            return _build_bulk_command_result(device=device, status="ERROR", detail=error_text)

        cache_result = _build_bulk_command_cache_result(
            device=device,
            command=command,
            status="SUCCESS",
            output=output,
            detail="",
            error="",
            duration=monotonic() - started_at,
        )
        with db_write_lock:
            _save_execution_result_with_retry(
                execution_id=execution.id,
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
        register_result(device, cache_result)
        return _build_bulk_command_result(device=device, status="SUCCESS", output=output)

    try:
        with ThreadPoolExecutor(max_workers=_get_bulk_command_workers_count(len(devices))) as executor:
            futures = [executor.submit(run_for_device, device) for device in devices]
            for future in as_completed(futures):
                future.result()
                update_progress()
    except Exception as exc:
        print(f"Task ID: {task_id} | Exception after ThreadPoolExecutor: {exc}")
        traceback.print_exc()
        BulkDeviceCommandExecution.objects.filter(task_id=task_id).update(
            status=BulkDeviceCommandExecution.STATUS_FAILURE,
            processed=processed,
            total=len(devices),
            progress=int(processed / total * 100),
            finished_at=timezone.now(),
        )
        raise

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
        "status": final_status,
        "progress": 100 if devices else 0,
        "total": len(devices),
        "processed": processed,
    }
