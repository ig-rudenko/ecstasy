import re
from typing import TypedDict


class VlanInfo(TypedDict):
    vlan_id: int
    name: str
    ports: list[str]


COLUMN_RE = re.compile(r"-+")
PORT_RE = re.compile(r"\b(?P<prefix>[A-Za-z]+)(?P<numbers>\d+(?:/\d+)*)(?:-(?P<end>\d+))?\b")


def _find_column_spans(lines: list[str]) -> tuple[list[tuple[int, int]], int] | None:
    """Find column positions by the separator row in show vlan output."""
    for line_number, line in enumerate(lines):
        spans = [match.span() for match in COLUMN_RE.finditer(line)]
        if len(spans) >= 5:
            return spans[:5], line_number
    return None


def _split_columns(line: str, spans: list[tuple[int, int]]) -> list[str]:
    """Split one fixed-width row by separator-derived column widths."""
    padded = line.rstrip().ljust(spans[-1][1])
    return [padded[start:end] for start, end in spans]


def _expand_port(port: str) -> list[str]:
    """Expand one Eltex port range into port names."""
    match = PORT_RE.fullmatch(port)
    if not match:
        return []

    prefix = match.group("prefix")
    numbers = match.group("numbers")
    range_end = match.group("end")
    if range_end is None:
        return [f"{prefix}{numbers}"]

    number_parts = numbers.split("/")
    range_start = int(number_parts[-1])
    end = int(range_end)
    step = 1 if range_start <= end else -1

    ports = []
    for port_number in range(range_start, end + step, step):
        expanded_parts = [*number_parts[:-1], str(port_number)]
        ports.append(f"{prefix}{'/'.join(expanded_parts)}")
    return ports


def _parse_ports(text: str) -> list[str]:
    """Parse comma-separated Eltex ports and ranges."""
    ports = []
    for raw_port in re.split(r"[\s,]+", text.strip()):
        if raw_port:
            ports.extend(_expand_port(raw_port))
    return ports


def _append_ports(vlan: VlanInfo, ports: list[str]) -> None:
    """Append ports preserving order and avoiding duplicates."""
    for port in ports:
        if port not in vlan["ports"]:
            vlan["ports"].append(port)


def parse_vlan_output(output: str) -> list[VlanInfo]:
    """Parse Eltex MES/ESR show vlan output."""
    lines = output.splitlines()
    columns = _find_column_spans(lines)
    if columns is None:
        return []

    spans, separator_line = columns
    vlans: list[VlanInfo] = []
    current_vlan: VlanInfo | None = None

    for line in lines[separator_line + 1 :]:
        vlan_id, name, tagged_ports, untagged_ports, _created_by = _split_columns(line, spans)
        vlan_id = vlan_id.strip()
        name = name.strip()
        ports = _parse_ports(f"{tagged_ports} {untagged_ports}")

        if vlan_id.isdigit():
            vlan: VlanInfo = {
                "vlan_id": int(vlan_id),
                "name": name,
                "ports": [],
            }
            current_vlan = vlan
            _append_ports(current_vlan, ports)
            vlans.append(current_vlan)
            continue

        if current_vlan is None:
            continue

        if name:
            current_vlan["name"] += name
        _append_ports(current_vlan, ports)

    return vlans
