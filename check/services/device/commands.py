import re
from ipaddress import IPv4Address

import orjson
from rest_framework.exceptions import ValidationError

from check.models import Devices, DeviceCommand
from devicemanager.device.interfaces import Interfaces


def validate_command(device: Devices, command: DeviceCommand, context: dict) -> str:

    def validate_port(port: str):
        port = port.strip()
        interfaces = Interfaces(orjson.loads(device.devicesinfo.interfaces or "[]"))
        return bool(interfaces[port].name)

    context_validators = {
        "ip": lambda ip: IPv4Address(ip),
        "port": validate_port,
        "mac": lambda mac: len(re.findall(r"[0-9a-f]", mac.strip().lower())) == 12,
    }
    cmd = command.command
    for key, validator in context_validators.items():
        if "{" + key + "}" in cmd:
            if key not in context:
                raise ValidationError(f"Missing {key} value")
            try:
                assert validator(context[key])
            except:  # noqa: E722
                raise ValidationError(f"Invalid {key} value")

            cmd = cmd.replace("{" + key + "}", context[key])
    return cmd


def execute_command(device: Devices, command: DeviceCommand, context):
    valid_command = validate_command(device, command, context)
    return device.connect().send_command(valid_command)
