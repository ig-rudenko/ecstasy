import re

from rest_framework.exceptions import ValidationError
from rest_framework.request import Request

from apps.app_settings.models import TracerouteConfig
from apps.check.models import Devices
from apps.check.services.device_coordinates import get_devices_coordinates
from apps.check.services.filters import filter_devices_qs_by_user
from apps.gathering.services.mac.traceroute import MacTraceroute
from apps.net_tools.services.finder import MultipleTraceroute, Traceroute
from apps.net_tools.services.network import TracerouteNetwork


def build_traceroute_graph_data(request: Request, query: dict) -> dict:
    """Build traceroute graph data shared by network and map visualizations."""
    mode = query["mode"]
    vlan = query.get("vlan")
    mac = query["mac"]
    mac_vlan = query.get("mac_vlan")
    empty_ports = query["ep"]
    only_admin_up = query["ad"]
    double_check = query["double_check"]
    graph_min_length = query["graph_min_length"]
    max_port_vlans = query["max_port_vlans"]
    trunk_filter_mode = query["trunk_filter_mode"]
    nodes_only = query["nodes_only"]
    device_name = query["device_name"]
    group = query["group"]

    if mode == "mac":
        mac_clean = "".join(re.findall(r"[0-9a-fA-F]+", mac)).lower()
        if len(mac_clean) != 12:
            raise ValidationError({"mac": "Invalid MAC address"})

        traceroute = MacTraceroute()
        return traceroute.get_mac_graph(
            mac=mac_clean,
            vlan=mac_vlan,
            device_name_filter=device_name,
            group_filter=group,
            show_empty_ports=empty_ports,
            graph_min_length=graph_min_length,
            nodes_only=nodes_only,
        )

    vlan_traceroute_settings = TracerouteConfig.load()
    devices_qs = filter_devices_qs_by_user(Devices.objects.all(), request.user)  # noqa

    if vlan_traceroute_settings.start_device:
        devices_names = tuple(map(str.strip, vlan_traceroute_settings.start_device.split("\n")))
        devices_qs = devices_qs.filter(name__in=devices_names)
    if vlan_traceroute_settings.start_device_regex:
        devices_qs = devices_qs.filter(name__iregex=vlan_traceroute_settings.start_device_regex)
    if vlan_traceroute_settings.device_ip_pattern:
        devices_qs = devices_qs.filter(ip__iregex=vlan_traceroute_settings.device_ip_pattern)

    if device_name:
        devices_qs = devices_qs.filter(name__icontains=device_name)
    if group:
        devices_qs = devices_qs.filter(group__name__icontains=group)

    tracert = MultipleTraceroute(
        finder=Traceroute(cache_timeout=vlan_traceroute_settings.cache_timeout),
        devices_queryset=devices_qs,
    )
    result = tracert.execute_traceroute(
        vlan=vlan if mode == "vlan" else None,
        empty_ports=empty_ports,
        double_check=double_check,
        only_admin_up=only_admin_up,
        graph_min_length=graph_min_length,
        max_port_vlans=max_port_vlans if mode == "vlan" else 0,
        trunk_filter_mode=trunk_filter_mode if mode == "vlan" else "off",
        find_device_pattern=vlan_traceroute_settings.find_device_pattern,
        device_name_filter=device_name,
        nodes_only=nodes_only,
    )

    if not result:
        return {
            "nodes": [],
            "edges": [],
            "options": {},
        }

    network = TracerouteNetwork()
    network.create_network(result, show_admin_down_ports=only_admin_up, nodes_only=nodes_only)

    return {
        "nodes": network.nodes,
        "edges": network.edges,
        "options": network.options,
    }


def build_traceroute_map_data(graph_data: dict) -> dict:
    """Convert graph nodes and edges to geographic traceroute payload."""
    graph_nodes = graph_data.get("nodes", [])
    graph_edges = graph_data.get("edges", [])
    graph_nodes_by_id = {
        str(node.get("id", "")).strip(): node
        for node in graph_nodes
        if str(node.get("id", "")).strip() and not node.get("hidden")
    }
    node_names = [
        str(node.get("id", "")).strip()
        for node in graph_nodes
        if str(node.get("id", "")).strip() and not node.get("hidden")
    ]
    coordinates = get_devices_coordinates(node_names)
    devices = _get_traceroute_map_devices(node_names)
    map_nodes = []
    skipped_nodes = []
    visible_ids = set()

    for node in graph_nodes:
        if node.get("hidden"):
            continue
        node_id = str(node.get("id", "")).strip()
        if not node_id:
            continue

        coords = coordinates.get(node_id)
        if not coords:
            continue

        try:
            lat = float(coords.lat)
            lon = float(coords.lon)
        except (TypeError, ValueError):
            skipped_nodes.append(
                {
                    "id": node_id,
                    "label": str(node.get("label", node_id)),
                    "reason": "invalid_zabbix_coordinates",
                }
            )
            continue

        map_nodes.append(
            {
                "id": node_id,
                "label": str(node.get("label", node_id)),
                "title": str(node.get("title", node.get("label", node_id)) or ""),
                "lat": lat,
                "lon": lon,
                "device": devices.get(node_id),
            }
        )
        visible_ids.add(node_id)

    inherited_count_by_parent: dict[str, int] = {}
    for node_id, node in graph_nodes_by_id.items():
        if node_id in visible_ids:
            continue
        if node_id in coordinates:
            continue

        parent_node = _find_traceroute_map_parent_node(node_id, graph_edges, map_nodes)
        if not parent_node:
            skipped_nodes.append(
                {
                    "id": node_id,
                    "label": str(node.get("label", node_id)),
                    "reason": "no_zabbix_coordinates",
                }
            )
            continue

        inherited_index = inherited_count_by_parent.get(parent_node["id"], 0)
        inherited_count_by_parent[parent_node["id"]] = inherited_index + 1
        lat, lon = _offset_traceroute_map_child_coordinates(
            parent_node["lat"], parent_node["lon"], inherited_index
        )
        map_nodes.append(
            {
                "id": node_id,
                "label": str(node.get("label", node_id)),
                "title": str(node.get("title", node.get("label", node_id)) or ""),
                "lat": lat,
                "lon": lon,
                "device": None,
                "inherited_from": parent_node["id"],
                "kind": "inherited",
            }
        )
        visible_ids.add(node_id)

    map_edges = [
        edge
        for edge in graph_edges
        if str(edge.get("from", "")).strip() in visible_ids and str(edge.get("to", "")).strip() in visible_ids
    ]
    data = {
        "nodes": map_nodes,
        "edges": map_edges,
        "skipped_nodes": skipped_nodes,
    }
    if "vlansInfo" in graph_data:
        data["vlansInfo"] = graph_data["vlansInfo"]
    return data


def _find_traceroute_map_parent_node(
    node_id: str, graph_edges: list[dict], map_nodes: list[dict]
) -> dict | None:
    """Find a coordinate-bearing neighbor for a node without its own coordinates."""
    map_nodes_by_id = {node["id"]: node for node in map_nodes}
    for edge in graph_edges:
        source = str(edge.get("from", "")).strip()
        target = str(edge.get("to", "")).strip()
        if source == node_id and target in map_nodes_by_id:
            return map_nodes_by_id[target]
        if target == node_id and source in map_nodes_by_id:
            return map_nodes_by_id[source]
    return None


def _offset_traceroute_map_child_coordinates(
    parent_lat: float, parent_lon: float, index: int
) -> tuple[float, float]:
    """Place inherited child nodes around the parent device coordinate."""
    offsets = [
        (0.00008, 0),
        (0, 0.00008),
        (-0.00008, 0),
        (0, -0.00008),
        (0.00006, 0.00006),
        (-0.00006, 0.00006),
        (-0.00006, -0.00006),
        (0.00006, -0.00006),
    ]
    ring = index // len(offsets) + 1
    lat_offset, lon_offset = offsets[index % len(offsets)]
    return parent_lat + lat_offset * ring, parent_lon + lon_offset * ring


def _get_traceroute_map_devices(node_names: list[str]) -> dict[str, dict]:
    """Return safe device details for traceroute map node popups."""
    return {
        device["name"]: {
            "name": device["name"],
            "ip": device["ip"],
            "vendor": device["vendor"] or "",
            "model": device["model"] or "",
            "group": device["group__name"] or "",
            "serial_number": device["serial_number"] or "",
            "os_version": device["os_version"] or "",
            "url": f"/device/{device['name']}",
        }
        for device in Devices.objects.filter(name__in=node_names).values(
            "name",
            "ip",
            "vendor",
            "model",
            "group__name",
            "serial_number",
            "os_version",
        )
    }
