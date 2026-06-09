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


if __name__ == "__main__":
    s = """Berezki_1a_SNR#show vlan
VLAN Name         Type       Media     Ports
---- ------------ ---------- --------- ----------------------------------------
1    default      Static     ENET      Ethernet1/0/49      Ethernet1/0/50
                                       Ethernet1/0/51      Ethernet1/0/52
191  Berezki-2_PPPoE Static     ENET      Ethernet1/0/3       Ethernet1/0/4
                                       Ethernet1/0/5       Ethernet1/0/6
                                       Ethernet1/0/7       Ethernet1/0/8
                                       Ethernet1/0/9       Ethernet1/0/10
                                       Ethernet1/0/11      Ethernet1/0/12
                                       Ethernet1/0/13      Ethernet1/0/14
                                       Ethernet1/0/15      Ethernet1/0/16
                                       Ethernet1/0/17      Ethernet1/0/18
                                       Ethernet1/0/19      Ethernet1/0/20
                                       Ethernet1/0/21      Ethernet1/0/22
                                       Ethernet1/0/23      Ethernet1/0/24
                                       Ethernet1/0/25      Ethernet1/0/26
                                       Ethernet1/0/27      Ethernet1/0/28
                                       Ethernet1/0/29      Ethernet1/0/30
                                       Ethernet1/0/31      Ethernet1/0/32
                                       Ethernet1/0/33      Ethernet1/0/34
                                       Ethernet1/0/35      Ethernet1/0/36
                                       Ethernet1/0/37      Ethernet1/0/38
                                       Ethernet1/0/39      Ethernet1/0/40
                                       Ethernet1/0/41      Ethernet1/0/42
                                       Ethernet1/0/43      Ethernet1/0/44
                                       Ethernet1/0/45      Ethernet1/0/46
                                       Ethernet1/0/47      Ethernet1/0/48
                                       Ethernet1/0/49(T)   Ethernet1/0/50(T)
                                       Ethernet1/0/51(T)   Ethernet1/0/52(T)
229  Control_VLAN36 Static     ENET      Ethernet1/0/49(T)   Ethernet1/0/50(T)
                                       Ethernet1/0/52(T)
241  Control_VLAN1 Static     ENET      Ethernet1/0/49(T)   Ethernet1/0/50(T)
                                       Ethernet1/0/52(T)
242  Control_VLAN2 Static     ENET      Ethernet1/0/49(T)   Ethernet1/0/50(T)
                                       Ethernet1/0/52(T)
244  Control_VLAN4 Static     ENET      Ethernet1/0/49(T)   Ethernet1/0/50(T)
                                       Ethernet1/0/51(T)   Ethernet1/0/52(T)
3819 ONS_Malikov  Static     ENET      Ethernet1/0/1       Ethernet1/0/49(T)
3820 260754_ONS_lunev Static     ENET      Ethernet1/0/2       Ethernet1/0/49(T)
"""

    print(parse_vlan_output(s))
