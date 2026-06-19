from django.conf import settings
from django.templatetags.static import static

UNFOLD: dict[str, object] = {
    "SITE_TITLE": "Ecstasy Admin",
    "SITE_HEADER": "Ecstasy",
    "SITE_SUBHEADER": "Network operations control",
    "SITE_URL": "/",
    "SITE_SYMBOL": "settings_ethernet",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "SHOW_BACK_BUTTON": True,
    "ENVIRONMENT": "ecstasy_project.admin_theme.environment_label",
    # "STYLES": ["ecstasy_project.admin_theme.admin_stylesheet"],
    "SITE_DROPDOWN": "ecstasy_project.admin_theme.site_dropdown",
    "SITE_FAVICONS": [
        {
            "href": "ecstasy_project.admin_theme.admin_favicon",
            "rel": "icon",
            "type": "image/x-icon",
        }
    ],
    "BORDER_RADIUS": "1.25rem",
    "COLORS": {
        "base": {
            "50": "oklch(98.4% 0.003 247.858)",
            "100": "oklch(96.8% 0.006 255.328)",
            "200": "oklch(92.9% 0.013 255.508)",
            "300": "oklch(86.8% 0.024 252.894)",
            "400": "oklch(70.2% 0.047 256.788)",
            "500": "oklch(55.2% 0.047 257.417)",
            "600": "oklch(44.6% 0.043 257.281)",
            "700": "oklch(37.2% 0.044 257.287)",
            "800": "oklch(27.8% 0.041 260.031)",
            "900": "oklch(20.9% 0.039 265.754)",
            "950": "oklch(13.1% 0.031 263.229)",
        },
        "primary": {
            "50": "oklch(97.6% 0.018 236.62)",
            "100": "oklch(94.3% 0.039 234.632)",
            "200": "oklch(89.1% 0.077 233.972)",
            "300": "oklch(81.2% 0.131 232.661)",
            "400": "oklch(72.1% 0.182 234.451)",
            "500": "oklch(63.5% 0.205 239.392)",
            "600": "oklch(55.9% 0.211 252.819)",
            "700": "oklch(48.9% 0.196 257.102)",
            "800": "oklch(42.4% 0.163 258.614)",
            "900": "oklch(38.1% 0.126 258.338)",
            "950": "oklch(28.2% 0.092 260.031)",
        },
        "font": {
            "subtle-light": "var(--color-base-500)",
            "subtle-dark": "var(--color-base-400)",
            "default-light": "var(--color-base-600)",
            "default-dark": "var(--color-base-300)",
            "important-light": "var(--color-base-900)",
            "important-dark": "var(--color-base-100)",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "command_search": True,
        "show_all_applications": True,
        "navigation": "ecstasy_project.admin_theme.sidebar_navigation",
    },
    "ACCOUNT": {
        "navigation": "ecstasy_project.admin_theme.account_links",
    },
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
            "title": "API документация",
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


def has_permission_to_model(app: str, model: str, permissions: set[str]):
    apps_permissions = filter(lambda item: item.startswith(f"{app}."), permissions)
    return any(filter(lambda item: model in str(item), apps_permissions))


def model_link(title: str, icon: str, app: str, model: str, permissions: set[str]):
    return {
        "title": title,
        "icon": icon,
        "link": f"/admin/{app}/{model}/",
        "permission": lambda r: has_permission_to_model(app, model, permissions),
    }


def sidebar_navigation(request):
    perms: set[str] = request.user.get_all_permissions()

    navigation = [
        {
            "title": "",
            "separator": False,
            "collapsible": False,
            "items": [
                {"title": "Главная админки", "icon": "dashboard", "link": "/admin/"},
                {"title": "Сайт", "icon": "language", "link": "/"},
                {"title": "API документация", "icon": "data_object", "link": "/api/swagger"},
            ],
        },
        {
            "title": "Users & Groups",
            "separator": False,
            "collapsible": True,
            "items": [
                model_link("Users", "people", "auth", "user", perms),
                model_link("Users profiles", "badge", "check", "profile", perms),
                model_link("Groups", "person", "auth", "group", perms),
            ],
        },
        {
            "title": "Device control",
            "separator": True,
            "collapsible": True,
            "items": [
                model_link("Devices", "dns", "check", "devices", perms),
                model_link("Device groups", "inventory_2", "check", "devicegroup", perms),
                model_link("Auth groups", "key", "check", "authgroup", perms),
                model_link("Access groups", "shield", "check", "accessgroup", perms),
                model_link("Device commands", "terminal", "check", "devicecommand", perms),
                model_link("Device interface comments", "comment", "check", "interfacescomments", perms),
                model_link("Media files", "perm_media", "check", "devicemedia", perms),
                model_link("Interface pattern rules", "memory", "check", "deviceinterfacepatternrule", perms),
                model_link("Users profiles", "badge", "check", "profile", perms),
                model_link("Users actions", "history", "check", "usersactions", perms),
                model_link("BRAS", "dns", "check", "bras", perms),
                model_link(
                    "Bulk device command executions", "memory", "check", "bulkdevicecommandexecution", perms
                ),
                model_link(
                    "Bulk command execution results",
                    "memory",
                    "check",
                    "bulkdevicecommandexecutionresult",
                    perms,
                ),
            ],
        },
        {
            "title": "Device information",
            "separator": False,
            "collapsible": True,
            "items": [
                model_link("Interfaces", "dns", "net_tools", "devicesinfo", perms),
                model_link("MAC addresses", "dns", "gathering", "macaddress", perms),
                model_link("VLANs", "dataset", "gathering", "vlan", perms),
                model_link("VLAN ports", "cable", "gathering", "vlanport", perms),
            ],
        },
        {
            "title": "Device discovery",
            "separator": False,
            "collapsible": True,
            "items": [
                model_link("Discovery attempts", "rule", "discovery", "discoveryattempt", perms),
                model_link("Discovery candidates", "fact_check", "discovery", "discoverycandidate", perms),
                model_link("Discovery profiles", "manage_search", "discovery", "discoveryprofile", perms),
                model_link("Discovery runs", "history", "discovery", "discoveryrun", perms),
            ],
        },
        {
            "title": "Device ring manager",
            "separator": False,
            "collapsible": True,
            "items": [
                model_link("Ring devs", "dns", "ring_manager", "ringdev", perms),
                model_link("Transport rings", "timeline", "ring_manager", "transportring", perms),
            ],
        },
        {
            "title": "GPON",
            "separator": True,
            "collapsible": True,
            "items": [
                model_link("OLT ports", "lan", "gpon", "oltstate", perms),
                model_link("Buildings", "apartment", "gpon", "houseb", perms),
                model_link("OLT to Buildings", "apartment", "gpon", "houseoltstate", perms),
                model_link("End3s", "device_hub", "gpon", "end3", perms),
                model_link("Tech capabilities", "settings_input_hdmi", "gpon", "techcapability", perms),
                model_link("Subscriber connections", "hub", "gpon", "subscriberconnection", perms),
                model_link("Customers", "group", "gpon", "customer", perms),
                model_link("Services", "sell", "gpon", "service", perms),
                model_link("Addresses", "home_pin", "gpon", "address", perms),
            ],
        },
        {
            "title": "Maps",
            "separator": False,
            "collapsible": True,
            "items": [
                model_link("Карты", "map", "maps", "maps", perms),
                model_link("Слои", "layers", "maps", "layers", perms),
            ],
        },
        {
            "title": "Notifications",
            "separator": False,
            "collapsible": True,
            "items": [
                model_link("Conditions", "rule", "notifications", "notificationcondition", perms),
                model_link("Telegram notifications", "send", "notifications", "telegramnotification", perms),
                model_link("Webhook notifications", "webhook", "notifications", "webhooknotification", perms),
            ],
        },
        {
            "title": "Dictionaries",
            "separator": False,
            "collapsible": True,
            "items": [
                model_link("VLAN names", "label", "net_tools", "vlanname", perms),
                model_link(
                    "Vlan traceroute desc name formats", "text_fields", "net_tools", "descnameformat", perms
                ),
            ],
        },
        {
            "title": "Settings",
            "separator": True,
            "collapsible": True,
            "items": [
                model_link(
                    "Devices for MAC search in ARP table",
                    "manage_search",
                    "net_tools",
                    "devicesformacsearch",
                    perms,
                ),
                model_link("Traceroute", "route", "app_settings", "tracerouteconfig", perms),
                model_link("VLAN traceroute node kind", "lan", "net_tools", "traceroutenodekind", perms),
                model_link(
                    "VLAN traceroute node style rules", "lan", "net_tools", "traceroutenodestylerule", perms
                ),
                model_link("Access rings", "tune", "app_settings", "accessringsettings", perms),
                model_link("Elastic", "article", "app_settings", "logselasticstacksettings", perms),
                model_link("Zabbix API", "monitor_heart", "app_settings", "zabbixconfig", perms),
            ],
        },
    ]

    if request.user.is_superuser:
        navigation.append(
            {
                "title": "System",
                "separator": True,
                "collapsible": False,
                "items": [
                    {"title": "API Tokens", "icon": "vpn_key", "link": "/admin/accounting/userapitoken/"},
                    {"title": "Periodical Tasks", "icon": "schedule", "link": "/admin/django_celery_beat/"},
                    {"title": "Cookie Sessions", "icon": "people", "link": "/admin/sessions/session/"},
                    {"title": "JWT Blacklist", "icon": "vpn_key", "link": "/admin/token_blacklist/"},
                    {"title": "Global News", "icon": "campaign", "link": "/admin/news/globalnews/"},
                ],
            },
        )

    return navigation
