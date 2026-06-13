from hashlib import sha256
from typing import Any

ZABBIX_CONFIG_VERSION_CACHE_KEY = "app_settings:zabbix_config_version"
ZABBIX_CONFIG_MISSING_VERSION = "missing"


def build_zabbix_config_version(config: Any) -> str:
    """Возвращает версию настроек Zabbix без сохранения самих настроек в cache."""
    if not config:
        return ZABBIX_CONFIG_MISSING_VERSION

    raw_value = "\0".join(
        (
            str(getattr(config, "url", "") or ""),
            str(getattr(config, "login", "") or ""),
            str(getattr(config, "password", "") or ""),
        )
    )
    return sha256(raw_value.encode("utf-8")).hexdigest()
