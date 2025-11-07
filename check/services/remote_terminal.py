from check.models import Profile


def get_console_url(profile: Profile, ip: str, name: str, cmd_protocol: str) -> str:
    """
    Возвращает ссылку на консоль подключения к устройству для указанного профиля
    """

    if not profile.console_access or not profile.console_url:
        return ""
    if cmd_protocol == "telnet":
        return (
            f"{profile.console_url}&command=/usr/share/connections/tc.sh {ip}" f"&title={ip} ({name}) telnet"
        )
    if cmd_protocol == "ssh":
        return f"{profile.console_url}&command=/usr/share/connections/sc.sh {ip}" f"&title={ip} ({name}) ssh"
    return profile.console_url
