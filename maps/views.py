import orjson
from datetime import datetime
from functools import wraps

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden, Http404
from pyzabbix import ZabbixAPI
from maps.models import Maps, Layers

from app_settings.models import ZabbixConfig


@login_required
def map_home(request):
    return render(
        request,
        "maps/home.html",
        {"maps": Maps.objects.filter(users=request.user)},
    )


def access_to_map(function):
    """
    ## Декоратор проверяет, есть ли пользователь в списке
    пользователей карты, и если да, то вызывает исходную функцию, либо 403

    :param function: Функция, которую нужно декорировать
    :return: Декоратор возвращает функцию-обертку.
    """

    @wraps(function)
    def wrapper(request, map_id, *args, **kwargs):
        try:
            # Получение объекта карты из базы данных.
            map_ = Maps.objects.get(id=map_id)
        except Maps.DoesNotExist:
            raise Http404

        # Проверяет, есть ли пользователь в списке пользователей карты.
        if request.user in map_.users.all():
            return function(request, map_, *args, **kwargs)

        # Возвращаем ответ с кодом состояния 403.
        return HttpResponseForbidden()

    return wrapper


@login_required
@access_to_map
def show_interactive_map(request, map_obj: Maps):
    """
    ## Возвращаем карту

    :param request: Это объект запроса, который отправляется в представление.
    Он содержит информацию о запросе, такую как метод HTTP, URL-адрес, заголовки и тело
    :param map_obj: Объект карты полученный от декоратора

    :return: Функция рендеринга карты или ошибка 404
    """

    # Проверяет тип карты. Если карта имеет тип "zabbix", то возвращает шаблон интерактивной карты.
    if map_obj.type == "zabbix":
        return render(request, "maps/interactive_map.html", {"map": map_obj})

    # Проверка, является ли карта внешней картой.
    if map_obj.type == "external":
        return render(request, "maps/external_map.html", {"map": map_obj})

    # Проверка, является ли карта файлом.
    if map_obj.type == "file":
        return render(
            request, "maps/external/" + map_obj.from_file.name.rsplit("/", 1)[-1]
        )

    # 404 если карта пустая
    raise Http404


@login_required
@access_to_map
def send_layers(request, map_obj: Maps):
    """
    ## Возвращаем слои на карте.

    :param request: Объект запроса
    :param map_obj: Объект карты полученный от декоратора
    """

    layers_name = []
    for layer in map_obj.layers.all():
        if layer.type == "zabbix":
            layers_name.append(layer.zabbix_group_name)
        elif layer.type == "file":
            layers_name.append(layer.name)

    return JsonResponse({"groups": layers_name})


def zabbix_get(
    group_id: int, group_name: str, zbx_settings: ZabbixConfig, current_layer: Layers
) -> dict:
    """
    ## Возвращает список хостов в группе Zabbix.

    :param group_id: ID группы, из которой вы хотите получить хосты
    :param group_name: Название группы, из которой вы хотите получить хосты
    :param current_layer: Слой - объект Layers
    :param zbx_settings: Объект ZabbixConfig, содержащий URL-адрес Zabbix-сервера, имя пользователя и пароль
    """
    result = {"type": "FeatureCollection", "features": []}

    with ZabbixAPI(server=zbx_settings.url) as z:
        z.login(user=zbx_settings.login, password=zbx_settings.password)
        hosts = z.host.get(
            groupids=group_id,
            selectInterfaces=["ip"],
            selectInventory=["location_lat", "location_lon"],
        )

    for host in hosts:
        if (
            host["inventory"]
            and host["inventory"]["location_lat"]
            and host["inventory"]["location_lon"]
            and host["status"] == "0"
        ):
            result["features"].append(
                {
                    "type": "Feature",
                    "id": host["hostid"],
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            host["inventory"]["location_lon"].replace(",", "."),
                            host["inventory"]["location_lat"].replace(",", "."),
                        ],
                    },
                    "properties": {
                        "name": host["name"],
                        "description": f"""
                        <div>
                        <a href="{zbx_settings.url}/zabbix.php?action=host.view&filter_name={host["name"]}&filter_ip=&
                                filter_dns=&filter_port=&filter_status=0&filter_evaltype=0&filter_tags%5B0%5D%5Btag%5D=&
                                filter_tags%5B0%5D%5Boperator%5D=0&filter_tags%5B0%5D%5Bvalue%5D=&
                                filter_maintenance_status=1&filter_show_suppressed=0&filter_set=1"
                            title="Посмотреть в Zabbix" style="color:black;font-size:18px" target="_blank">
                            {host["name"]}
                        </a>
                        </div>
                        """,
                        "group": group_name,
                        "figure": "circle",
                        "iconName": current_layer.marker_icon_name,
                        "style": {
                            "radius": current_layer.points_size,
                            "fillColor": current_layer.points_color,
                            "color": current_layer.points_border_color,
                            "weight": 1,
                            "opacity": 1,
                            "fillOpacity": 1,
                        },
                    },
                }
            )

    return result


@login_required
@access_to_map
def render_interactive_map(request, map_obj: Maps):
    """
    ## Возвращаем координаты узлов сети, которые необходимо разместить на карте с идентификатором ```map_id```

    :param request: Объект запроса
    :param map_obj: Объект карты полученный от декоратора
    """

    # Загрузка объекта ZabbixConfig из базы данных.
    zbx_settings = ZabbixConfig.load()

    layers_data = []

    with ZabbixAPI(server=zbx_settings.url) as z:
        z.login(user=zbx_settings.login, password=zbx_settings.password)

        for layer in map_obj.layers.all():  # Проходимся по введенным именам групп

            # Если слой покрывает группу Zabbix
            if layer.type == "zabbix":
                layer_data = {
                    "name": layer.zabbix_group_name,
                    "type": "zabbix",
                    "features": {},
                }

                # Находим группу в Zabbix
                group = z.hostgroup.get(filter={"name": layer.zabbix_group_name})

                if group:  # Если такая группа существует

                    # Добавление результата функции `zabbix_get` в список `geo_json["features"]`
                    layer_data["features"] = zabbix_get(
                        group_id=int(group[0]["groupid"]),
                        group_name=layer.zabbix_group_name,
                        zbx_settings=zbx_settings,
                        current_layer=layer,
                    )
                # Сохраняем данные слоя
                layers_data.append(layer_data)

            # Для внешних карт.
            elif layer.type == "file":

                # Создаем стиль для слоя
                layer_data = {
                    "name": layer.name,
                    "type": "geojson",
                    "properties": {
                        "Polygon": {
                            "FillColor": layer.polygon_fill_color,
                            "Color": layer.polygon_border_color,
                            "Opacity": layer.polygon_opacity,
                        },
                        "Marker": {
                            "FillColor": layer.points_color,
                            "BorderColor": layer.points_border_color,
                            "Size": layer.points_size,
                            "IconName": layer.marker_icon_name,
                        },
                    },
                    "features": {},
                }

                # Читаем содержимое файла
                with layer.from_file.open("r") as file:
                    try:
                        layer_data["features"] = orjson.loads(file.read())
                    except orjson.JSONDecodeError:
                        # Пропускаем файл, который не получилось прочитать
                        continue

                # Сохраняем данные слоя
                layers_data.append(layer_data)

    return JsonResponse(layers_data, safe=False)


def get_hosts_with_problem(zabbix_session: ZabbixAPI, zabbix_group_id: str) -> list:
    """
    Определяет недоступные узлы сети для конкретной группы Zabbix, а также их подтверждения проблем
    :param zabbix_session: Zabbix сессия
    :param zabbix_group_id: ID Группы в Zabbix
    :return: словарь из ID тех узлов, которые недоступны в этой группе и подтверждения по этим проблемам
    """
    problems = []

    # Все узлы сети в группе
    hosts_id = [
        host["hostid"]
        # Получение всех хостов в группе с заданным идентификатором группы.
        for host in zabbix_session.host.get(
            groupids=[zabbix_group_id], output=["hostid"], filter={"status": "0"}
        )
    ]

    # Получение проблемы узла сети из Zabbix.
    device_problems_list = zabbix_session.problem.get(
        hostids=hosts_id,
        selectAcknowledges="extend",
        output="extend",
        filter={"name": "Оборудование недоступно"},
    )

    # Перебор списка проблем.
    for device_problem in device_problems_list:

        # Проверяем, есть ли проблема с устройством.
        if device_problem:

            # ID узла сети, у которого проблема.
            host_id = zabbix_session.item.get(
                triggerids=[device_problem["objectid"]], output=["hostid", "name"]
            )

            acknowledges = []
            # Проверка наличия подтверждений в списке device_problem.
            if device_problem["acknowledges"]:
                # Проверка наличия подтверждений в списке device_problem.
                acknowledges = [
                    [
                        ack["message"],
                        datetime.fromtimestamp(int(ack["clock"])).strftime(
                            "%H:%M %d-%m-%Y"
                        ),
                    ]
                    for ack in device_problem["acknowledges"]
                ] or []

            # Добавление словаря {"id": "host_id", "acknowledges": [["datetime", "text"], ... ]}
            # в список `проблем`
            problems.append({"id": host_id[0]["hostid"], "acknowledges": acknowledges})

    return problems


@login_required
@access_to_map
def update_interactive_map(request, map_obj: Maps):
    """
    # Проверяем какие из узлов сети недоступны на интерактивной карте с заданным идентификатором

    Возвращаем JSON ответ с проблемными узлами сети и подтверждение проблем (если они есть в Zabbix):

        {
            "problems": [
                {"id": "host_id", "acknowledges": [["datetime", "text"], ... ]},
                {"id": "host_id", "acknowledges": [["datetime", "text"], ... ]},
                ...
            ]

        }

    :param request: Объект запроса
    :param map_obj: Объект карты полученный от декоратора
    """

    zbx_settings = ZabbixConfig.load()

    groups = [
        gr["zabbix_group_name"]
        for gr in map_obj.layers.all().values("zabbix_group_name")
    ]

    problem_hosts = []

    with ZabbixAPI(server=zbx_settings.url) as z:
        for g in groups:  # Проходимся по введенным именам групп
            z.login(user=zbx_settings.login, password=zbx_settings.password)
            group = z.hostgroup.get(filter={"name": g})  # Находим группу в Zabbix
            if group:  # Если такая группа существует
                problem_hosts += get_hosts_with_problem(
                    zabbix_session=z, zabbix_group_id=group[0]["groupid"]
                )

    return JsonResponse({"problems": problem_hosts})
