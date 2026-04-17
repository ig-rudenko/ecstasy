import re
import time
import uuid
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from ipaddress import IPv4Address
from typing import Any

import orjson
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.exceptions import ValidationError

from devicemanager.device.interfaces import Interfaces
from devicemanager.device_connector.types import RemoteCommand, RemoteCommandCondition
from devicemanager.multifactory import DeviceMultiFactory
from devicemanager.vendors import BaseDevice

from ...models import (
    BulkDeviceCommandExecution,
    BulkDeviceCommandExecutionResult,
    DeviceCommand,
    Devices,
)


@dataclass(frozen=True)
class ContextValidator:
    key: str
    pattern: re.Pattern
    validate: Callable[[re.Match[str], str], None]
    clean: Callable[[Any, Devices], str]


def normalize_device_vendor(value) -> str:
    """Return normalized device vendor for comparisons."""
    return str(value or "").strip().casefold()


def normalize_device_model(value) -> str:
    """Return normalized device model for regex comparisons."""
    return str(value or "").strip()


def clean_device_port(port: str, device: Devices) -> str:
    """
    Приводит порт в необходимый формат в зависимости от вендора и модели оборудования.
    """
    dev_types_by_vendor: list[type[BaseDevice]] = []

    # Проходим по фабрике оборудования и смотрим все доступные типы оборудований.
    for dev_type in DeviceMultiFactory.support_devices():
        if device.vendor is not None and dev_type.vendor.lower() == device.vendor.lower():
            # Оставляем только для нашего вендора.
            dev_types_by_vendor.append(dev_type)

    dev_types_without_sub_models: list[type[BaseDevice]] = []
    for dev_type in dev_types_by_vendor:
        if dev_type.supported_models is not None and dev_type.supported_models.match(str(device.model)):
            # Если нашли точное соответствие вендора и модели оборудования.
            return dev_type.normalize_interface_name(port)

        if dev_type.supported_models is None:
            # Создаём список типов оборудования, у которых нет `supported_models`
            # т.е. они подходят для всех моделей.
            dev_types_without_sub_models.append(dev_type)

    # Если не нашли чёткого сопоставления модели ранее,
    # проверяем есть ли для данного вендора уникальные типы оборудования и берём у самого первого
    if dev_types_without_sub_models:
        return dev_types_by_vendor[0].normalize_interface_name(port)

    # Если ничего не найдено, то возвращаем название как есть.
    return port


def get_command_model_pattern(command: DeviceCommand) -> re.Pattern | None:
    """Compile command model regexp safely."""
    if not command.model_regexp:
        return None

    return re.compile(command.model_regexp.strip(), re.IGNORECASE)


def validate_device_port(device: Devices, port: str) -> None:
    port = port.strip()
    interfaces = Interfaces(orjson.loads(device.devicesinfo.interfaces or "[]"))
    if not interfaces[port].name:
        raise ValidationError("Вы указали не существующий порт")


def validate_ip(ip: str) -> None:
    try:
        IPv4Address(ip.strip())
    except ValueError as exc:
        raise ValidationError("Неверный формат IP") from exc


def validate_mac(mac: str) -> None:
    if not len(re.findall(r"[0-9a-f]", mac.strip().lower())) == 12:
        raise ValidationError("Неверный формат MAC")


def validate_word(word: str) -> None:
    if not re.match(r"^\S+$", word):
        raise ValidationError("Не должно быть пробельных символов")


def validate_number(number_string: str, min_value: str, max_value: str) -> None:
    try:
        number = int(str(number_string).strip())
    except ValueError as exc:
        raise ValidationError("Необходимо указать целое число") from exc

    if min_value and number < int(min_value):
        raise ValidationError(f"Число должно быть больше или равно {min_value}")

    if max_value and number > int(max_value):
        raise ValidationError(f"Число должно быть меньше или равно {max_value}")


def validate_command(device: Devices, command: str, context: dict) -> list[RemoteCommand]:
    """Validate command macros for one device and render command list."""
    context_validators: list[ContextValidator] = [
        ContextValidator(
            key="ip",
            pattern=re.compile(r"\{ip(?:#(?P<name>\S+?)?)?}"),
            validate=lambda m, ip: validate_ip(ip),
            clean=lambda v, d: str(v),
        ),
        ContextValidator(
            key="port",
            pattern=re.compile(r"\{port(?:#(?P<name>\S+?)?)?}"),
            validate=lambda m, port: validate_device_port(device, port),
            clean=lambda v, d: clean_device_port(v, d),
        ),
        ContextValidator(
            key="mac",
            pattern=re.compile(r"\{mac(?:#(?P<name>\S+?)?)?}"),
            validate=lambda m, mac: validate_mac(mac),
            clean=lambda v, d: str(v),
        ),
        ContextValidator(
            key="number",
            pattern=re.compile(r"\{number(?::(?P<start>-?\d+)?)?(?::(?P<end>-?\d+)?)?(?:#(?P<name>\S+?)?)?}"),
            validate=lambda m, v: validate_number(v, m.group("start"), m.group("end")),
            clean=lambda v, d: str(v),
        ),
        ContextValidator(
            key="word",
            pattern=re.compile(r"\{word(?:#(?P<name>\S+?)?)?}"),
            validate=lambda m, word: validate_word(word),
            clean=lambda v, d: str(v),
        ),
        ContextValidator(
            key="if",
            pattern=re.compile(r"\{if(?::(?P<condition>.+?)?)?(?:(?<!\\):(?P<command>.*?)?)?(?<!\\)}"),
            validate=lambda m, word: validate_word(word),
            clean=lambda v, d: str(v),
        ),
    ]

    default_key = "_"

    match: re.Match | None = None
    first = True

    validated_commands: list[RemoteCommand] = []

    for cmd_line in command.splitlines():
        valid_cmd_line: RemoteCommand = {"command": cmd_line.strip(), "conditions": []}

        for validator in context_validators:
            while match or first:
                match = validator.pattern.search(valid_cmd_line["command"])
                if match is None:
                    first = True
                    break

                first = False

                if validator.key == "if":
                    condition: RemoteCommandCondition = {
                        "expect": str(match.group("condition")),
                        "command": str(match.group("command")),
                    }
                    # Убираем экранируемые символы
                    condition["expect"] = condition["expect"].replace("\\\\", "\\")

                    valid_cmd_line["conditions"].append(condition)

                    start_pos, end_pos = match.span()
                    valid_cmd_line["command"] = (
                        valid_cmd_line["command"][:start_pos] + valid_cmd_line["command"][end_pos:]
                    ).strip()
                    continue

                key_context: dict = context.get(validator.key, {})

                if not isinstance(key_context, dict):
                    valid_format = {"key": "value"}
                    raise ValidationError(
                        f"Неверный формат данных для ключа {validator.key} - `{key_context}`. "
                        f"Должен быть формат: `{valid_format}`"
                    )

                key = match.group("name") or default_key
                value = str(key_context.get(key)).strip()

                if value is None:
                    raise ValidationError(f"Необходимо указать ключ `{key}` для параметра {validator.key}")

                validator.validate(match, value)
                clean_value = validator.clean(value, device)

                start_pos, end_pos = match.span()

                valid_cmd_line["command"] = (
                    valid_cmd_line["command"][:start_pos]
                    + str(clean_value)
                    + valid_cmd_line["command"][end_pos:]
                )

        validated_commands.append(valid_cmd_line)

    return validated_commands


def execute_command(device: Devices, command: DeviceCommand, context: dict) -> str:
    """Execute command on one device and return merged output."""
    validated_commands = validate_command(device, command.command, context)

    outputs = device.connect().execute_commands_list(validated_commands)
    return "\n\n".join(outputs)


def get_command_text_for_audit(device: Devices, command: DeviceCommand, context: dict) -> str:
    """Return rendered command text for audit storage."""
    validated_commands = validate_command(device, command.command, context)
    return "\n".join(item["command"] for item in validated_commands)


def is_command_available_for_device(command: DeviceCommand, device: Devices) -> bool:
    """Check whether the command can be used for the given device."""
    device_vendor = normalize_device_vendor(device.vendor)
    device_model = normalize_device_model(device.model)
    command_vendor = normalize_device_vendor(command.device_vendor)

    if not device_vendor or (str(command.model_regexp or "").strip() and not device_model):
        return False

    if command_vendor != device_vendor:
        return False

    try:
        model_pattern = get_command_model_pattern(command)
    except re.error:
        return False

    return model_pattern is None or model_pattern.search(device_model) is not None


def get_available_commands_for_device(user: User, device: Devices) -> list[DeviceCommand]:
    """Return commands available for the user and device."""
    if not device.vendor:
        return []

    commands = DeviceCommand.objects.filter(device_vendor__iexact=str(device.vendor).strip())
    if not user.is_superuser:
        commands = commands.filter(perm_groups__user=user)

    return [command for command in commands.distinct() if is_command_available_for_device(command, device)]


def get_available_command_for_device(user: User, device: Devices, command_id: int) -> DeviceCommand | None:
    """Return a single available command for the user and device."""
    for command in get_available_commands_for_device(user, device):
        if command.id == command_id:
            return command
    return None


def get_device_command_task_results_cache_key(task_id: str) -> str:
    """Build a cache key for bulk command execution results."""
    return f"device-command-task:{task_id}:results"


def get_device_command_task_lock_cache_key(task_id: str) -> str:
    """Build a cache key for bulk command execution lock."""
    return f"device-command-task:{task_id}:lock"


@contextmanager
def device_command_task_cache_lock(task_id: str, timeout: int = 10, expires: int = 30):
    """Lock cache updates for a bulk command task."""
    lock_key = get_device_command_task_lock_cache_key(task_id)
    lock_value = str(uuid.uuid4())
    start_time = time.monotonic()

    while not cache.add(lock_key, lock_value, timeout=expires):
        if time.monotonic() - start_time > timeout:
            raise TimeoutError("Timed out while waiting for bulk command cache lock")
        time.sleep(0.05)

    try:
        yield
    finally:
        if cache.get(lock_key) == lock_value:
            cache.delete(lock_key)


def init_device_command_task_results_cache(task_id: str) -> None:
    """Initialize task results cache."""
    cache.set(get_device_command_task_results_cache_key(task_id), {}, timeout=None)


def set_device_command_task_results(task_id: str, results: dict[str, dict]) -> None:
    """Replace all task results in cache."""
    cache.set(get_device_command_task_results_cache_key(task_id), dict(results), timeout=None)


def update_device_command_task_result(task_id: str, device_id: int, result: dict) -> None:
    """Safely update task results cache for one device."""
    with device_command_task_cache_lock(task_id):
        cache_key = get_device_command_task_results_cache_key(task_id)
        current_results = dict(cache.get(cache_key, {}))
        current_results[str(device_id)] = result
        cache.set(cache_key, current_results, timeout=None)


def get_device_command_task_results(task_id: str) -> dict[str, dict]:
    """Return all cached task results."""
    return dict(cache.get(get_device_command_task_results_cache_key(task_id), {}))


def dispatch_bulk_execute_command_task(
    command: DeviceCommand,
    devices: list[Devices],
    context: dict,
    user_id: int,
) -> dict:
    """Send a celery task for bulk command execution."""
    from ...tasks import execute_bulk_device_command_task

    eligible_devices: list[Devices] = []
    skipped_devices: list[dict] = []

    for device in devices:
        if is_command_available_for_device(command, device):
            eligible_devices.append(device)
            continue

        skipped_devices.append(
            {
                "deviceId": device.id,
                "deviceName": device.name,
                "detail": "Command is unavailable for this device",
            }
        )

    if not eligible_devices:
        raise ValidationError({"detail": "Нет оборудования, подходящего для выполнения команды"})

    task_id = str(uuid.uuid4())
    execution = BulkDeviceCommandExecution.objects.create(
        task_id=task_id,
        user_id=user_id,
        command=command,
        command_name=command.name,
        command_body=command.command,
        context=context,
        status=BulkDeviceCommandExecution.STATUS_PENDING,
        total=len(eligible_devices),
    )

    task = execute_bulk_device_command_task.apply_async(
        args=(
            command.id,
            [device.id for device in eligible_devices],
            context,
            user_id,
        ),
        task_id=task_id,
    )

    BulkDeviceCommandExecutionResult.objects.bulk_create(
        [
            BulkDeviceCommandExecutionResult(
                execution=execution,
                device_id=device["deviceId"],
                device_name=device["deviceName"],
                status=BulkDeviceCommandExecutionResult.STATUS_SKIPPED,
                detail=device["detail"],
            )
            for device in skipped_devices
        ]
    )

    return {
        "taskId": task.id,
        "devices": [
            {
                "deviceId": device.id,
                "deviceName": device.name,
            }
            for device in eligible_devices
        ],
        "skipped": skipped_devices,
    }
