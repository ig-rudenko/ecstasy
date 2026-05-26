from ..models import Profile


def get_device_console_url(profile: Profile, *, username: str, ip: str, name: str, cmd_protocol: str) -> str:
    """
    Возвращает ссылку на консоль подключения к устройству для указанного профиля
    """

    if not profile.console_access or not profile.device_console_url:
        return ""
    return profile.device_console_url.format(ip=ip, name=name, protocol=cmd_protocol, username=username)
