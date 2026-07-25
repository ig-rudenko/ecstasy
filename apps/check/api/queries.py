from dataclasses import dataclass


@dataclass(kw_only=True, slots=True)
class DeviceInterfaceQuery:
    current_status: bool
    vlans: bool
    check_status: bool
    add_links: bool
    add_comments: bool
    add_zabbix_graph: bool
