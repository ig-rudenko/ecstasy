from django.apps import apps
from django.conf import settings
from django.templatetags.static import static
from django.urls import NoReverseMatch, reverse_lazy

APP_GROUPS = {
    "check": {"title": "Оборудование", "icon": "memory"},
    "gathering": {"title": "Сбор данных", "icon": "hub"},
    "gpon": {"title": "GPON", "icon": "device_hub"},
    "maps": {"title": "Карты", "icon": "map"},
    "app_settings": {"title": "Настройки платформы", "icon": "tune"},
    "accounting": {"title": "API и доступ", "icon": "vpn_key"},
    "news": {"title": "Новости", "icon": "newspaper"},
    "notifications": {"title": "Уведомления", "icon": "notifications"},
    "ring_manager": {"title": "Кольца", "icon": "timeline"},
    "net_tools": {"title": "Сетевые справочники", "icon": "lan"},
}

MODEL_ICONS = {
    "DeviceGroup": "inventory_2",
    "AuthGroup": "key",
    "Devices": "dns",
    "AccessGroup": "shield",
    "DeviceMedia": "perm_media",
    "Bras": "dns",
    "Profile": "badge",
    "UsersActions": "history",
    "InterfacesComments": "comment",
    "DeviceCommand": "terminal",
    "MacAddress": "fingerprint",
    "Vlan": "dataset",
    "VlanPort": "cable",
    "Address": "home_pin",
    "OLTState": "lan",
    "HouseOLTState": "apartment",
    "HouseB": "apartment",
    "End3": "device_hub",
    "TechCapability": "settings_input_hdmi",
    "Customer": "group",
    "Service": "sell",
    "SubscriberConnection": "hub",
    "Layers": "layers",
    "Maps": "map",
    "LogsElasticStackSettings": "article",
    "ZabbixConfig": "monitor_heart",
    "VlanTracerouteConfig": "route",
    "AccessRingSettings": "tune",
    "UserAPIToken": "vpn_key",
    "DescNameFormat": "text_fields",
    "VlanName": "label",
    "DevicesForMacSearch": "manage_search",
    "DevicesInfo": "dns",
    "GlobalNews": "campaign",
    "WebhookNotification": "webhook",
    "TelegramNotification": "send",
    "NotificationTrigger": "bolt",
    "NotificationCondition": "rule",
    "TransportRing": "timeline",
    "RingDev": "dns",
}


def admin_stylesheet(_request):
    return static("admin/css/ecstasy-unfold.css")


def admin_favicon(_request):
    return static("flavico.ico")


def environment_label(_request):
    if settings.ENV == "prod":
        return ["Production", "success"]
    if settings.DEBUG:
        return ["Development", "warning"]
    return [settings.ENV.upper(), "info"]


def site_dropdown(_request):
    return [
        {
            "title": "Открыть сайт",
            "icon": "arrow_outward",
            "link": "/",
            "attrs": {"target": "_blank", "rel": "noopener noreferrer"},
        },
        {
            "title": "Устройства",
            "icon": "memory",
            "link": "/devices",
            "attrs": {"target": "_blank", "rel": "noopener noreferrer"},
        },
        {
            "title": "API документация",
            "icon": "data_object",
            "link": "/api/swagger",
            "attrs": {"target": "_blank", "rel": "noopener noreferrer"},
        },
    ]


def account_links(request):
    links = [
        {
            "title": "Главная Ecstasy",
            "link": "/",
        },
        {
            "title": "Swagger UI",
            "link": "/api/swagger",
        },
    ]

    if request.user.is_staff:
        links.append(
            {
                "title": "Устройства",
                "link": "/devices",
            }
        )

    return links


def _app_model_items(app_label: str):
    """Build sidebar links for registered admin models in an app."""
    app_config = apps.get_app_config(app_label)
    items = []

    for model in sorted(app_config.get_models(), key=lambda item: item._meta.verbose_name_plural):
        try:
            link = reverse_lazy(f"admin:{app_label}_{model._meta.model_name}_changelist")
        except NoReverseMatch:
            continue

        items.append(
            {
                "title": str(model._meta.verbose_name_plural).capitalize(),
                "icon": MODEL_ICONS.get(model.__name__, APP_GROUPS[app_label]["icon"]),
                "link": str(link),
            }
        )

    return items


def _installed_app_labels() -> list[str]:
    """Return project app labels from INSTALLED_APPS in a stable order."""
    installed_labels = [
        app_path.removeprefix("apps.") for app_path in settings.INSTALLED_APPS if app_path.startswith("apps.")
    ]
    ordered_labels = [label for label in APP_GROUPS if label in installed_labels]
    ordered_labels.extend(label for label in installed_labels if label not in ordered_labels)
    return ordered_labels


def sidebar_navigation(request):
    operations = [
        {
            "title": "Главная админки",
            "icon": "dashboard",
            "link": "/admin/",
        },
        {
            "title": "Сайт",
            "icon": "language",
            "link": "/",
        },
        {
            "title": "Swagger UI",
            "icon": "terminal",
            "link": "/api/swagger",
        },
    ]

    navigation = [
        {
            "title": "Операции",
            "separator": False,
            "collapsible": False,
            "items": operations,
        },
        {
            "title": "Пользователи и группы",
            "separator": False,
            "collapsible": True,
            "items": [
                {
                    "title": "Пользователи",
                    "icon": "person",
                    "link": "/admin/auth/user/",
                },
                {
                    "title": "Группы",
                    "icon": "person",
                    "link": "/admin/auth/group/",
                },
            ],
        },
    ]

    for index, app_label in enumerate(_installed_app_labels()):
        if app_label not in APP_GROUPS:
            continue

        items = _app_model_items(app_label)
        if not items:
            continue

        navigation.append(
            {
                "title": APP_GROUPS[app_label]["title"],
                "separator": index == 0,
                "collapsible": True,
                "items": items,
            }
        )

    if request.user.is_superuser:
        navigation.append(
            {
                "title": "Системное",
                "separator": False,
                "collapsible": True,
                "items": [
                    {
                        "title": "Celery Beat",
                        "icon": "schedule",
                        "link": "/admin/django_celery_beat/",
                    },
                    {
                        "title": "Импорт и экспорт",
                        "icon": "import_export",
                        "link": "/admin/check/devices/",
                    },
                ],
            }
        )

    return navigation
