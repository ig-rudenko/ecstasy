import re
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from ipaddress import IPv4Address
from typing import Any

import orjson
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ValidationError as DjangoValidationError
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


@dataclass(frozen=True)
class CommandMacro:
    """One recognized macro in a command template."""

    kind: str
    text: str
    start: int
    end: int
    name: str | None = None
    name_start: int | None = None
    name_end: int | None = None
    condition: str | None = None
    response: str | None = None
    min_value: str | None = None
    max_value: str | None = None


IP_MACRO_PATTERN = re.compile(r"\{ip(?:#(?P<name>\S+?)?)?}")
PORT_MACRO_PATTERN = re.compile(r"\{port(?:#(?P<name>\S+?)?)?}")
MAC_MACRO_PATTERN = re.compile(r"\{mac(?:#(?P<name>\S+?)?)?}")
NUMBER_MACRO_PATTERN = re.compile(
    r"\{number(?::(?P<start>-?\d+)?)?(?::(?P<end>-?\d+)?)?(?:#(?P<name>\S+?)?)?}"
)
WORD_MACRO_PATTERN = re.compile(r"\{word(?:#(?P<name>\S+?)?)?}")
CONDITION_MACRO_PATTERN = re.compile(r"\{if(?::(?P<condition>.+?)?)?(?:(?<!\\):(?P<command>.*?)?)?(?<!\\)}")
COMMAND_MACRO_PATTERNS = (
    ("ip", IP_MACRO_PATTERN),
    ("port", PORT_MACRO_PATTERN),
    ("mac", MAC_MACRO_PATTERN),
    ("number", NUMBER_MACRO_PATTERN),
    ("word", WORD_MACRO_PATTERN),
    ("if", CONDITION_MACRO_PATTERN),
)


def _match_command_macro(command: str, position: int) -> tuple[str, re.Match[str]] | None:
    """Return a recognized macro starting at the given position."""
    for kind, pattern in COMMAND_MACRO_PATTERNS:
        match = pattern.match(command, position)
        if match is not None:
            return kind, match
    return None


def _is_escaped_opening_brace(command: str, position: int) -> bool:
    """Return whether an opening brace is preceded by an odd slash count."""
    slash_count = 0
    position -= 1
    while position >= 0 and command[position] == "\\":
        slash_count += 1
        position -= 1
    return slash_count % 2 == 1


def iter_command_macros(command: str) -> Iterator[CommandMacro]:
    """Yield recognized, unescaped macros from a command template."""
    position = 0

    while position < len(command):
        if command[position] != "{" or _is_escaped_opening_brace(command, position):
            position += 1
            continue

        macro_match = _match_command_macro(command, position)
        if macro_match is None:
            position += 1
            continue

        kind, match = macro_match
        name = match.groupdict().get("name")
        name_start = None
        name_end = None
        if name is not None:
            name_start, name_end = match.span("name")

        yield CommandMacro(
            kind=kind,
            text=match.group(0),
            start=match.start(),
            end=match.end(),
            name=name,
            name_start=name_start,
            name_end=name_end,
            condition=match.groupdict().get("condition"),
            response=match.groupdict().get("command"),
            min_value=match.groupdict().get("start"),
            max_value=match.groupdict().get("end"),
        )
        position = match.end()


def _validate_command_macro(match: re.Match[str]) -> None:
    """Validate constraints encoded in one recognized command macro."""
    if match.re is NUMBER_MACRO_PATTERN:
        start = match.group("start")
        end = match.group("end")
        if start and end and int(start) > int(end):
            raise DjangoValidationError(
                f"В макросе {match.group(0)} минимальное значение не может быть больше максимального."
            )

    if match.re is CONDITION_MACRO_PATTERN:
        condition = match.group("condition")
        response = match.group("command")
        if condition is None or response is None:
            raise DjangoValidationError(
                f"Условный макрос {match.group(0)} должен иметь формат {{if:ожидание:ответ}}."
            )
        try:
            re.compile(condition.replace("\\\\", "\\"))
        except re.error as exc:
            raise DjangoValidationError(
                f"В условном макросе {match.group(0)} указано неверное регулярное выражение: {exc}."
            ) from exc


def _prepare_command_template(command: str) -> tuple[str, str]:
    """Validate macros and mask escaped opening braces before rendering."""
    escaped_brace_marker = "\0escaped-opening-brace\0"
    while escaped_brace_marker in command:
        escaped_brace_marker += "\0"

    prepared_command: list[str] = []
    position = 0

    while position < len(command):
        if command[position] == "\\":
            slash_end = position
            while slash_end < len(command) and command[slash_end] == "\\":
                slash_end += 1

            slash_count = slash_end - position
            if slash_end < len(command) and command[slash_end] == "{":
                prepared_command.append("\\" * (slash_count // 2))
                if slash_count % 2:
                    prepared_command.append(escaped_brace_marker)
                    position = slash_end + 1
                    continue

                position = slash_end
                continue

            prepared_command.append("\\" * slash_count)
            position = slash_end
            continue

        if command[position] == "{":
            macro_match = _match_command_macro(command, position)
            if macro_match is None:
                raise DjangoValidationError(
                    "Команда содержит неизвестный или незавершённый макрос. "
                    "Для обычного символа `{` используйте `\\{`. "
                    "Доступны: {port}, {ip}, {mac}, {number}, {word}, {if:ожидание:ответ}."
                )

            _, match = macro_match
            _validate_command_macro(match)
            prepared_command.append(match.group(0))
            position = match.end()
            continue

        prepared_command.append(command[position])
        position += 1

    return "".join(prepared_command), escaped_brace_marker


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


def validate_command_template(command: str) -> None:
    """Validate command macros without requiring a device or context values."""
    _prepare_command_template(command)


def validate_command(device: Devices, command: str, context: dict) -> list[RemoteCommand]:
    """Validate command macros for one device and render command list."""
    try:
        prepared_command, escaped_brace_marker = _prepare_command_template(command)
    except DjangoValidationError as exc:
        raise ValidationError(exc.messages) from exc

    context_validators: list[ContextValidator] = [
        ContextValidator(
            key="ip",
            pattern=IP_MACRO_PATTERN,
            validate=lambda m, ip: validate_ip(ip),
            clean=lambda v, d: str(v),
        ),
        ContextValidator(
            key="port",
            pattern=PORT_MACRO_PATTERN,
            validate=lambda m, port: validate_device_port(device, port),
            clean=lambda v, d: clean_device_port(v, d),
        ),
        ContextValidator(
            key="mac",
            pattern=MAC_MACRO_PATTERN,
            validate=lambda m, mac: validate_mac(mac),
            clean=lambda v, d: str(v),
        ),
        ContextValidator(
            key="number",
            pattern=NUMBER_MACRO_PATTERN,
            validate=lambda m, v: validate_number(v, m.group("start"), m.group("end")),
            clean=lambda v, d: str(v),
        ),
        ContextValidator(
            key="word",
            pattern=WORD_MACRO_PATTERN,
            validate=lambda m, word: validate_word(word),
            clean=lambda v, d: str(v),
        ),
        ContextValidator(
            key="if",
            pattern=CONDITION_MACRO_PATTERN,
            validate=lambda m, word: validate_word(word),
            clean=lambda v, d: str(v),
        ),
    ]

    default_key = "_"

    match: re.Match | None = None
    first = True

    validated_commands: list[RemoteCommand] = []

    for cmd_line in prepared_command.splitlines():
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

        valid_cmd_line["command"] = valid_cmd_line["command"].replace(escaped_brace_marker, "{")
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
