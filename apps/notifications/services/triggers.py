from enum import StrEnum


class TriggerNames(StrEnum):
    device_port_reload = "device:port:reload"
    device_port_down = "device:port:down"
    device_port_up = "device:port:up"
    device_port_change_description = "device:port:change_description"
    device_port_set_poe_status = "device:port:set_poe_status"
    device_port_change_adsl_profile = "device:port:change_adsl_profile"

    @staticmethod
    def get_name_for_device_port_status(status: str) -> str:
        if status == "up":
            return TriggerNames.device_port_up.name
        if status == "down":
            return TriggerNames.device_port_down.name
        if status == "reload":
            return TriggerNames.device_port_reload.name
        raise ValueError(f"Unknown port status {status}")
