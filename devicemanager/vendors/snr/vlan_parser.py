import re
from typing import TypedDict


class VlanInfo(TypedDict):
    vlan_id: int
    name: str
    ports: list[str]


VLAN_ROW_RE = re.compile(
    r"""
    ^(?P<bridge>\S+)\s+
    (?P<vlan_id>\d+)\s+
    (?P<name>.*?)
    \s+
    (?P<state>ACTIVE|INACTIVE|DISABLED)
    \s+
    (?P<hw_status>Up|Down|-)
    \s*
    (?P<ports>.*)$
    """,
    re.VERBOSE,
)

PORT_RE = re.compile(r"\b(?P<name>[a-zA-Z]+\d+)\([ut]\)")


def _parse_ports(text: str) -> list[str]:
    return [match.group("name") for match in PORT_RE.finditer(text)]


def _is_header_or_separator(line: str) -> bool:
    stripped = line.strip()

    return (
        not stripped
        or stripped.startswith("Bridge")
        or stripped.startswith("(u)-")
        or stripped.startswith("=======")
    )


def _is_port_continuation_line(line: str) -> bool:
    stripped = line.strip()

    if not stripped:
        return False

    ports = _parse_ports(stripped)

    if not ports:
        return False

    without_ports = PORT_RE.sub("", stripped).strip()
    return without_ports == ""


def _is_vlan_name_continuation_line(line: str) -> bool:
    return bool(line) and line[0].isspace()


def parse_vlan_output(output: str) -> list[VlanInfo]:
    vlans: list[VlanInfo] = []
    current_vlan: VlanInfo | None = None

    for raw_line in output.splitlines():
        line = raw_line.rstrip()

        if _is_header_or_separator(line):
            continue

        row_match = VLAN_ROW_RE.match(line)

        if row_match:
            vlan: VlanInfo = {
                "vlan_id": int(row_match.group("vlan_id")),
                "name": row_match.group("name").strip(),
                "ports": _parse_ports(row_match.group("ports")),
            }

            current_vlan = vlan
            vlans.append(vlan)
            continue

        if current_vlan is None:
            continue

        if _is_port_continuation_line(line):
            current_vlan["ports"].extend(_parse_ports(line))
            continue

        if _is_vlan_name_continuation_line(line):
            current_vlan["name"] += line.strip()
            continue

    return vlans
