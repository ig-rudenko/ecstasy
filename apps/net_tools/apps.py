from django.apps import AppConfig
from django.db.models.signals import post_migrate


def register_task(*args, **kwargs) -> None:
    """Registers periodic/background tasks after migrations."""
    # pylint: disable-next=import-outside-toplevel
    from .tasks import InterfacesScanTask

    InterfacesScanTask.register_task()


def ensure_default_node_kinds(*args, **kwargs) -> None:
    """Creates default traceroute node kinds and style rules if missing."""
    # pylint: disable-next=import-outside-toplevel
    from .models import TracerouteNodeKind, TracerouteNodeStyleRule

    kind_defaults = (
        {
            "code": "empty_port",
            "name": "Empty Port",
            "marker_prefix": "p:(",
            "marker_suffix": ")",
            "value_source": TracerouteNodeKind.ValueSource.MARKER_BODY,
            "hide_when_nodes_only": True,
            "description": "Service node for empty ports in traceroute graph.",
        },
        {
            "code": "unknown_description",
            "name": "Unknown Description",
            "marker_prefix": "d:(",
            "marker_suffix": ")",
            "value_source": TracerouteNodeKind.ValueSource.MARKER_BODY,
            "hide_when_nodes_only": True,
            "description": "Service node for unresolved interface descriptions.",
        },
    )

    kinds_by_code: dict[str, TracerouteNodeKind] = {}
    for item in kind_defaults:
        code = item["code"]
        defaults = {key: value for key, value in item.items() if key != "code"}
        kind, _ = TracerouteNodeKind.objects.get_or_create(code=code, defaults=defaults)
        kinds_by_code[code] = kind

    style_defaults = (
        {
            "name": "Default Empty Port Style",
            "is_active": True,
            "priority": 20,
            "node_kind": kinds_by_code["empty_port"],
            "match_type": TracerouteNodeStyleRule.MatchType.CONTAINS,
            "pattern": "",
            "shape": TracerouteNodeStyleRule.Shape.TRIANGLE,
            "color_background": "#b8f5c2",
            "color_border": "#2f9e44",
            "color_font": "#0f5132",
            "stop_processing": True,
            "description": "Auto-created default style for empty ports.",
        },
        {
            "name": "Default Unknown Description Style",
            "is_active": True,
            "priority": 30,
            "node_kind": kinds_by_code["unknown_description"],
            "match_type": TracerouteNodeStyleRule.MatchType.CONTAINS,
            "pattern": "",
            "shape": TracerouteNodeStyleRule.Shape.DOT,
            "color_background": "#ffe3e3",
            "color_border": "#c92a2a",
            "color_font": "#7f1d1d",
            "stop_processing": True,
            "description": "Auto-created default style for unresolved descriptions.",
        },
        {
            "name": "Default CORE Style",
            "is_active": True,
            "priority": 10,
            "node_kind": None,
            "match_type": TracerouteNodeStyleRule.MatchType.REGEX,
            "pattern": "(?i)(core|-cr)",
            "shape": TracerouteNodeStyleRule.Shape.DIAMOND,
            "fixed_value": 70,
            "color_background": "#f3d9fa",
            "color_border": "#9c36b5",
            "color_font": "#4a044e",
            "stop_processing": True,
            "description": "Auto-created default style for CORE devices.",
        },
    )

    for item in style_defaults:
        name = item["name"]
        defaults = {key: value for key, value in item.items() if key != "name"}
        TracerouteNodeStyleRule.objects.get_or_create(name=name, defaults=defaults)


class FindDescConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.net_tools"

    def ready(self):
        # pylint: disable-next=import-outside-toplevel
        from .new_permissions import create_permission

        post_migrate.connect(
            create_permission,
            sender=self,
            weak=False,
            dispatch_uid="net_tools.create_permission",
        )
        post_migrate.connect(
            register_task,
            sender=self,
            weak=False,
            dispatch_uid="net_tools.register_task",
        )
        post_migrate.connect(
            ensure_default_node_kinds,
            sender=self,
            weak=False,
            dispatch_uid="net_tools.ensure_default_node_kinds",
        )
