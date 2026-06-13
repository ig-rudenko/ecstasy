from django.conf import settings
from django.templatetags.static import static


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
