import os

TRUE_VALUES = {"1", "true", "yes"}


def env_bool(name: str, default: bool = False) -> bool:
    """Return a boolean setting from an environment variable."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in TRUE_VALUES


def env_int(name: str, default: int) -> int:
    """Return an integer setting from an environment variable."""
    return int(os.getenv(name, str(default)))
