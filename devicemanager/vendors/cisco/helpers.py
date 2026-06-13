import re


def parse_nexus_ram_utilization(output: str) -> float:
    match = re.search(
        r"([\d.]+)\s*([KMGTP]?)[Bb]?\s+total,\s+([\d.]+)\s*([KMGTP]?)[Bb]?\s+used",
        output,
        re.IGNORECASE,
    )

    if not match:
        return -1

    total_value, total_unit = match.group(1), match.group(2).upper()
    used_value, used_unit = match.group(3), match.group(4).upper()

    units = {
        "": 1,
        "K": 1024,
        "M": 1024**2,
        "G": 1024**3,
        "T": 1024**4,
        "P": 1024**5,
    }

    total_bytes = float(total_value) * units[total_unit]
    used_bytes = float(used_value) * units[used_unit]

    return round((used_bytes / total_bytes) * 100, 2)


def parse_nexus_cpu_utilization(info: str) -> tuple:
    """
    ## Возвращает загрузку CPU
    """

    cpu_util_match = re.findall(
        r"CPU\d+ states\s+:\s+(?P<user_cpu>\S+)%\s+user,\s+(?P<kernel_cpu>\S+)%\s+kernel",
        info,
    )
    try:
        return tuple(round(float(line[0]) + float(line[1])) for line in cpu_util_match)
    except ValueError:
        return ()


def parse_nexus_flash_usage_percent(output: str) -> float:
    used_match = re.search(r"(\d+)\s+bytes\s+used", output, re.IGNORECASE)
    total_match = re.search(r"(\d+)\s+bytes\s+total", output, re.IGNORECASE)

    if not used_match or not total_match:
        raise ValueError("Invalid flash usage format")

    used_bytes = int(used_match.group(1))
    total_bytes = int(total_match.group(1))

    if total_bytes == 0:
        raise ValueError("Total bytes cannot be zero")

    return round((used_bytes / total_bytes) * 100, 2)
