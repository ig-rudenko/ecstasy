import re
from collections.abc import Callable
from dataclasses import dataclass
from ipaddress import IPv4Address

import orjson
from rest_framework.exceptions import ValidationError

from check.models import DeviceCommand, Devices
from devicemanager.device.interfaces import Interfaces


@dataclass(frozen=True)
class ContextValidator:
    key: str
    pattern: re.Pattern
    validate: Callable


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


def validate_command(device: Devices, command: str, context: dict) -> str:
    context_validators: list[ContextValidator] = [
        ContextValidator(
            key="ip",
            pattern=re.compile(r"\{ip(?:#(?P<name>\S+)?)?}"),
            validate=lambda m, ip: validate_ip(ip),
        ),
        ContextValidator(
            key="port",
            pattern=re.compile(r"\{port(?:#(?P<name>\S+)?)?}"),
            validate=lambda m, port: validate_device_port(device, port),
        ),
        ContextValidator(
            key="mac",
            pattern=re.compile(r"\{mac(?:#(?P<name>\S+)?)?}"),
            validate=lambda m, mac: validate_mac(mac),
        ),
        ContextValidator(
            key="number",
            pattern=re.compile(r"\{number(?::(?P<start>-?\d+)?)?(?::(?P<end>-?\d+)?)?(?:#(?P<name>\S+)?)?}"),
            validate=lambda m, v: validate_number(v, m.group("start"), m.group("end")),
        ),
        ContextValidator(
            key="word",
            pattern=re.compile(r"\{word(?:#(?P<name>\S+)?)?}"),
            validate=lambda m, word: validate_word(word),
        ),
    ]

    default_key = "_"

    match: re.Match | None = None
    first = True

    for validator in context_validators:
        while match or first:
            match = validator.pattern.search(command)
            if match is None:
                first = True
                break

            first = False

            key_context: dict = context.get(validator.key, {})

            key = match.group("name") or default_key
            value = str(key_context.get(key)).strip()

            if value is None:
                raise ValidationError(f"Необходимо указать ключ `{key}` для параметра {validator.key}")

            validator.validate(match, value)

            start_pos, end_pos = match.span()

            command = command[:start_pos] + str(value) + command[end_pos:]

    return command


def execute_command(device: Devices, command: DeviceCommand, context: dict) -> str:
    valid_command = validate_command(device, command.command, context)
    cmd_lines = valid_command.split("\n")

    if len(cmd_lines) > 1:
        outputs = device.connect().execute_commands_list(cmd_lines)
        return "\n".join(outputs)

    return device.connect().execute_command(valid_command)
