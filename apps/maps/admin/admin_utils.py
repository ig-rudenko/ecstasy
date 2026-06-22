import os
from collections import Counter
from typing import cast

import orjson
from pyzabbix import ZabbixAPIException
from requests import RequestException

from devicemanager.device.zabbix_api import zabbix_api

svg_file_icon = """<svg style="vertical-align: middle" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
  <path d="M14 4.5V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h5.5L14 4.5zm-3 0A1.5 1.5 0 0 1 9.5 3V1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V4.5h-2z"/>
  <path d="M8.646 6.646a.5.5 0 0 1 .708 0l2 2a.5.5 0 0 1 0 .708l-2 2a.5.5 0 0 1-.708-.708L10.293 9 8.646 7.354a.5.5 0 0 1 0-.708zm-1.292 0a.5.5 0 0 0-.708 0l-2 2a.5.5 0 0 0 0 .708l2 2a.5.5 0 0 0 .708-.708L5.707 9l1.647-1.646a.5.5 0 0 0 0-.708z"/>
</svg>"""

svg_zabbix_icon = """<svg style="vertical-align: middle" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 64 64">
  <path d="M0 0h64v64H0z" fill="#d31f26"/>
  <path d="M18.8 15.382h26.393v3.424l-21.24 26.027h21.744v3.784H18.293v-3.43l21.24-26.02H18.8z" fill="#fff"/>
</svg>"""

svg_device_icon = """<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="bi bi-pc-horizontal" viewBox="0 0 16 16">
  <path d="M1 6a1 1 0 0 0-1 1v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1V7a1 1 0 0 0-1-1zm11.5 1a.5.5 0 1 1 0 1 .5.5 0 0 1 0-1m2 0a.5.5 0 1 1 0 1 .5.5 0 0 1 0-1M1 7.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5M1.25 9h5.5a.25.25 0 0 1 0 .5h-5.5a.25.25 0 0 1 0-.5"/>
</svg>"""


def get_icons_html_code(fill_color: str, stroke_color: str, icon_name=None) -> str | tuple[str | tuple, ...]:
    """Return icon html by name, or all icons as choices when name is None."""
    icons = [
        {
            "name": "circle-fill",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" viewBox="0 0 16 16">
                <circle cx="8" cy="8" r="7" stroke="{stroke_color}" />
            </svg>""",
        },
        {
            "name": "triangle",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" viewBox="0 0 16 17">
              <path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z" stroke="{stroke_color}" />
            </svg>""",
        },
        {
            "name": "diamond",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" viewBox="-1 -1 18 18">
              <path stroke="{stroke_color}" fill-rule="evenodd" d="M6.95.435c.58-.58 1.52-.58 2.1 0l6.515 6.516c.58.58.58 1.519 0 2.098L9.05 15.565c-.58.58-1.519.58-2.098 0L.435 9.05a1.482 1.482 0 0 1 0-2.098L6.95.435z" />
            </svg>""",
        },
        {
            "name": "square",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" viewBox="-1 -1 18 18">
              <path stroke="{stroke_color}" d="M0 2a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2z"/>
            </svg>""",
        },
        {
            "name": "pentagon",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" viewBox="-1 -1 18 18">
              <path stroke="{stroke_color}" d="M7.685.256a.5.5 0 0 1 .63 0l7.421 6.03a.5.5 0 0 1 .162.538l-2.788 8.827a.5.5 0 0 1-.476.349H3.366a.5.5 0 0 1-.476-.35L.102 6.825a.5.5 0 0 1 .162-.538l7.42-6.03Z"/>
            </svg>""",
        },
        {
            "name": "hexagon",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" viewBox="-1 -1 18 18">
              <path stroke="{stroke_color}" fill-rule="evenodd" d="M8.5.134a1 1 0 0 0-1 0l-6 3.577a1 1 0 0 0-.5.866v6.846a1 1 0 0 0 .5.866l6 3.577a1 1 0 0 0 1 0l6-3.577a1 1 0 0 0 .5-.866V4.577a1 1 0 0 0-.5-.866z"/>
            </svg>""",
        },
        {
            "name": "record-circle",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" viewBox="0 0 16 16">
              <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
              <path d="M11 8a3 3 0 1 1-6 0 3 3 0 0 1 6 0z" stroke="{stroke_color}" />
            </svg>""",
        },
        {
            "name": "half-circle",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" viewBox="0 0 16 16">
              <path d="M8 15A7 7 0 1 0 8 1zm0 1A8 8 0 1 1 8 0a8 8 0 0 1 0 16"/>
            </svg>""",
        },
        {
            "name": "wrench-circle",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" viewBox="0 0 16 16">
              <path d="M12.496 8a4.491 4.491 0 0 1-1.703 3.526L9.497 8.5l2.959-1.11c.027.2.04.403.04.61Z"/>
              <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0Zm-1 0a7 7 0 1 0-13.202 3.249l1.988-1.657a4.5 4.5 0 0 1 7.537-4.623L7.497 6.5l1 2.5 1.333 3.11c-.56.251-1.18.39-1.833.39a4.49 4.49 0 0 1-1.592-.29L4.747 14.2A7 7 0 0 0 15 8Zm-8.295.139a.25.25 0 0 0-.288-.376l-1.5.5.159.474.808-.27-.595.894a.25.25 0 0 0 .287.376l.808-.27-.595.894a.25.25 0 0 0 .287.376l1.5-.5-.159-.474-.808.27.596-.894a.25.25 0 0 0-.288-.376l-.808.27.596-.894Z"/>
            </svg>""",
        },
        {
            "name": "circle-in-triangle",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" viewBox="0 0 16 16">
              <path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z" stroke="{2}" />
              <circle cx="8" cy="10" r="4" stroke="{stroke_color}" />
            </svg>""",
        },
        {
            "name": "warning",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" viewBox="-1 -1 18 18">
              <path stroke="{stroke_color}" d="M9.05.435c-.58-.58-1.52-.58-2.1 0L.436 6.95c-.58.58-.58 1.519 0 2.098l6.516 6.516c.58.58 1.519.58 2.098 0l6.516-6.516c.58-.58.58-1.519 0-2.098zM8 4c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995A.905.905 0 0 1 8 4m.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/>
            </svg>""",
        },
    ]
    if icon_name is None:
        from django.utils.safestring import mark_safe

        return tuple((ico["name"], mark_safe(ico["code"])) for ico in icons)
    for ico in icons:
        if icon_name == ico["name"]:
            return ico["code"]
    return ""


def get_polygon(fill_color: str):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="{fill_color}" class="bi bi-heptagon-half" viewBox="0 0 16 16">
          <path d="M7.779.052a.5.5 0 0 1 .442 0l6.015 2.97a.5.5 0 0 1 .267.34l1.485 6.676a.5.5 0 0 1-.093.415l-4.162 5.354a.5.5 0 0 1-.395.193H4.662a.5.5 0 0 1-.395-.193L.105 10.453a.5.5 0 0 1-.093-.415l1.485-6.676a.5.5 0 0 1 .267-.34L7.779.053zM8 15h3.093l3.868-4.975-1.383-6.212L8 1.058V15z"/>
        </svg>"""


def get_line(fill_color: str):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="{fill_color}" class="bi bi-share-fill" viewBox="0 0 16 16">
          <path d="M11 2.5a2.5 2.5 0 1 1 .603 1.628l-6.718 3.12a2.499 2.499 0 0 1 0 1.504l6.718 3.12a2.5 2.5 0 1 1-.488.876l-6.718-3.12a2.5 2.5 0 1 1 0-3.256l6.718-3.12A2.5 2.5 0 0 1 11 2.5z"/>
        </svg>"""


def get_zabbix_groups():
    """Return (name, name) list for all zabbix groups."""
    try:
        with zabbix_api.connect() as zbx:
            groups = zbx.hostgroup.get(output=["name"])
    except (RequestException, ZabbixAPIException):
        groups = []
    return ((g["name"], g["name"]) for g in groups)


def parse_layer_file(file_path) -> dict:
    """Parse geojson layer and return counters grouped by geometry type."""
    if not os.path.exists(path=file_path):
        return {}
    with open(file_path, "rb") as file:
        data = orjson.loads(file.read())
    if not isinstance(data, dict) or "features" not in data:
        return {}

    feature_types: dict = {}
    total_count = 0
    for feature in data["features"]:
        if not isinstance(feature, dict):
            continue
        total_count += 1
        feature_geometry = feature.get("geometry")
        if feature_geometry is None:
            continue
        feature_type = feature_geometry.get("type", "None")
        feature_types.setdefault(feature_type, {"count": 0, "colours": Counter()})
        feature_types[feature_type]["count"] += 1
        colour = (
            feature.get("properties", {}).get("fill", "")
            or feature.get("properties", {}).get("marker-color", "")
            or feature.get("properties", {}).get("stroke", "")
        )
        if colour:
            feature_types[feature_type]["colours"][colour] += 1

    for _, data in feature_types.items():
        data["percent"] = round(data["count"] / total_count, 2)
    return feature_types


def resolve_marker_icon(points_color: str, points_border_color: str, icon_name: str) -> str:
    """Resolve one marker icon as html string."""
    return cast(
        str,
        get_icons_html_code(points_color, points_border_color, icon_name=icon_name),
    )
