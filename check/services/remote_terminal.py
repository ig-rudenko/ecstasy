from check.models import Devices, Profile


def get_console_url(profile: Profile, device: Devices) -> str:
    """
    Возвращает ссылку на консоль подключения к устройству для указанного профиля
    :param profile: Profile.
    :param device: Devices.
    :return: Ссылка на консоль подключения.
    """
    if not profile.console_access or not profile.console_url:
        return ""
    if device.cmd_protocol == "telnet":
        return (
            f"{profile.console_url}&command=/usr/share/connections/tc.sh {device.ip}"
            f"&title={device.ip} ({device.name}) telnet"
        )
    elif device.cmd_protocol == "ssh":
        return (
            f"{profile.console_url}&command=/usr/share/connections/sc.sh {device.ip}"
            f"&title={device.ip} ({device.name}) ssh"
        )
    else:
        return profile.console_url
