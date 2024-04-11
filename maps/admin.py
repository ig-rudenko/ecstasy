import os
from collections import Counter
from typing import cast

import orjson
from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import SafeString, mark_safe
from pyzabbix import ZabbixAPIException
from requests import RequestException

from devicemanager.device.zabbix_api import zabbix_api
from .models import Layers, Maps

svg_file_icon = """<svg style="vertical-align: middle" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
  <path d="M14 4.5V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h5.5L14 4.5zm-3 0A1.5 1.5 0 0 1 9.5 3V1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V4.5h-2z"/>
  <path d="M8.646 6.646a.5.5 0 0 1 .708 0l2 2a.5.5 0 0 1 0 .708l-2 2a.5.5 0 0 1-.708-.708L10.293 9 8.646 7.354a.5.5 0 0 1 0-.708zm-1.292 0a.5.5 0 0 0-.708 0l-2 2a.5.5 0 0 0 0 .708l2 2a.5.5 0 0 0 .708-.708L5.707 9l1.647-1.646a.5.5 0 0 0 0-.708z"/>
</svg>"""

svg_zabbix_icon = """<svg style="vertical-align: middle" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 64 64">
  <path d="M0 0h64v64H0z" fill="#d31f26"/>
  <path d="M18.8 15.382h26.393v3.424l-21.24 26.027h21.744v3.784H18.293v-3.43l21.24-26.02H18.8z" fill="#fff"/>
</svg>"""


def get_icons_html_code(fill_color: str, stroke_color: str, icon_name=None) -> str | tuple[str | tuple, ...]:
    """
    Функция возвращает HTML-код для различных иконок на основе входных параметров.

    :param fill_color: Цвет заливки значка в шестнадцатеричном формате (например, "#FF0000" для красного).
    :param stroke_color: Параметр цвета обводки — это цвет контура или границы значка.
    :param icon_name: Имя значка, для которого вы хотите получить HTML-код.
     Если нет, функция вернет HTML-коды для всех доступных значков.
    :return: Если `icon_name` равно `None`, возвращается объект-генератор, который выдает кортежи имен значков и
     соответствующий им HTML-код. Если `icon_name` не равно `None`, возвращается код HTML для указанного значка.

    """
    icons = [
        # Circle fill
        {
            "name": "circle-fill",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" viewBox="0 0 16 16">
                <circle cx="8" cy="8" r="7" stroke="{stroke_color}" />
            </svg>""",
        },
        # Треугольник
        {
            "name": "triangle",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" viewBox="0 0 16 17">
              <path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z" stroke="{stroke_color}" />
            </svg>""",
        },
        # Ромб
        {
            "name": "diamond",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" viewBox="-1 -1 18 18">
              <path stroke="{stroke_color}" fill-rule="evenodd" d="M6.95.435c.58-.58 1.52-.58 2.1 0l6.515 6.516c.58.58.58 1.519 0 2.098L9.05 15.565c-.58.58-1.519.58-2.098 0L.435 9.05a1.482 1.482 0 0 1 0-2.098L6.95.435z" />
            </svg>""",
        },
        # Квадрат
        {
            "name": "square",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" viewBox="-1 -1 18 18">
              <path stroke="{stroke_color}" d="M0 2a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2z"/>
            </svg>""",
        },
        # Пентагон
        {
            "name": "pentagon",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" viewBox="-1 -1 18 18">
              <path stroke="{stroke_color}" d="M7.685.256a.5.5 0 0 1 .63 0l7.421 6.03a.5.5 0 0 1 .162.538l-2.788 8.827a.5.5 0 0 1-.476.349H3.366a.5.5 0 0 1-.476-.35L.102 6.825a.5.5 0 0 1 .162-.538l7.42-6.03Z"/>
            </svg>""",
        },
        # Гексагон
        {
            "name": "hexagon",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" viewBox="-1 -1 18 18">
              <path stroke="{stroke_color}" fill-rule="evenodd" d="M8.5.134a1 1 0 0 0-1 0l-6 3.577a1 1 0 0 0-.5.866v6.846a1 1 0 0 0 .5.866l6 3.577a1 1 0 0 0 1 0l6-3.577a1 1 0 0 0 .5-.866V4.577a1 1 0 0 0-.5-.866z"/>
            </svg>""",
        },
        # Record circle
        {
            "name": "record-circle",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" viewBox="0 0 16 16">
              <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
              <path d="M11 8a3 3 0 1 1-6 0 3 3 0 0 1 6 0z" stroke="{stroke_color}" />
            </svg>""",
        },
        # Кольцо
        {
            "name": "half-circle",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" viewBox="0 0 16 16">
              <path d="M8 15A7 7 0 1 0 8 1zm0 1A8 8 0 1 1 8 0a8 8 0 0 1 0 16"/>
            </svg>""",
        },
        # Гаечный ключ регулируемый круг
        {
            "name": "wrench-circle",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" viewBox="0 0 16 16">
              <path d="M12.496 8a4.491 4.491 0 0 1-1.703 3.526L9.497 8.5l2.959-1.11c.027.2.04.403.04.61Z"/>
              <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0Zm-1 0a7 7 0 1 0-13.202 3.249l1.988-1.657a4.5 4.5 0 0 1 7.537-4.623L7.497 6.5l1 2.5 1.333 3.11c-.56.251-1.18.39-1.833.39a4.49 4.49 0 0 1-1.592-.29L4.747 14.2A7 7 0 0 0 15 8Zm-8.295.139a.25.25 0 0 0-.288-.376l-1.5.5.159.474.808-.27-.595.894a.25.25 0 0 0 .287.376l.808-.27-.595.894a.25.25 0 0 0 .287.376l1.5-.5-.159-.474-.808.27.596-.894a.25.25 0 0 0-.288-.376l-.808.27.596-.894Z"/>
            </svg>""",
        },
        # Круг в треугольнике
        {
            "name": "circle-in-triangle",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" viewBox="0 0 16 16">
              <path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z" stroke="{2}" />
              <circle cx="8" cy="10" r="4" stroke="{stroke_color}" />
            </svg>""",
        },
        # Warning
        {
            "name": "warning",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" viewBox="-1 -1 18 18">
              <path stroke="{stroke_color}" d="M9.05.435c-.58-.58-1.52-.58-2.1 0L.436 6.95c-.58.58-.58 1.519 0 2.098l6.516 6.516c.58.58 1.519.58 2.098 0l6.516-6.516c.58-.58.58-1.519 0-2.098zM8 4c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995A.905.905 0 0 1 8 4m.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/>
            </svg>""",
        },
    ]

    if icon_name is None:
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
    """
    Возвращает список кортежей вида (group_name, group_name) для всех групп в Zabbix
    :return: Список кортежей.
    """
    try:
        with zabbix_api.connect() as zbx:
            # Получение всех групп узлов сети из Zabbix.
            groups = zbx.hostgroup.get(output=["name"])
    except (RequestException, ZabbixAPIException) as exc:
        groups = []

    choices_groups = ((g["name"], g["name"]) for g in groups)
    return choices_groups


class LayerFrom(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Динамически смотрим группы из Zabbix
        self.fields["zabbix_group_name"] = forms.ChoiceField(
            label="Выберите группу Zabbix", choices=get_zabbix_groups(), required=False
        )
        icons = get_icons_html_code(self.instance.points_color, self.instance.points_border_color)

        self.fields["marker_icon_name"] = forms.ChoiceField(
            label="Выберите иконку",
            widget=forms.RadioSelect,
            choices=icons,
            initial=icons[0],
        )

    class Meta:
        model = Layers
        fields = "__all__"
        widgets = {
            "points_color": forms.TextInput(attrs={"type": "color"}),
            "points_border_color": forms.TextInput(attrs={"type": "color"}),
            "polygon_opacity": forms.TextInput(),
            "polygon_fill_color": forms.TextInput(attrs={"type": "color"}),
            "polygon_border_color": forms.TextInput(attrs={"type": "color"}),
        }


@admin.register(Layers)
class LayersAdmin(admin.ModelAdmin):
    list_display = ("layer_name", "icon", "layer_type")
    form = LayerFrom

    fieldsets = (
        ("Описание", {"fields": ("name", "description")}),
        (
            "Из файла",
            {
                "fields": ("from_file",),
            },
        ),
        (
            "Из Zabbix",
            {"fields": ("zabbix_group_name",)},
        ),
        (
            "Настройки по умолчанию для Маркера",
            {
                "fields": (
                    "points_color",
                    "points_border_color",
                    "points_size",
                    "marker_icon_name",
                )
            },
        ),
        (
            "Настройки по умолчанию для Полигона",
            {
                "fields": (
                    "polygon_opacity",
                    "polygon_fill_color",
                    "polygon_border_color",
                )
            },
        ),
    )

    @admin.display(description="Название слоя")
    def layer_name(self, instance: Layers) -> str:
        if instance.type == "zabbix":
            return format_html(f"{svg_zabbix_icon} {instance.name}")
        if instance.type == "file":
            return format_html(f"{svg_file_icon} {instance.name}")

        return instance.name

    @admin.display(description="Структура")
    def icon(self, instance: Layers) -> SafeString:
        """
        Эта функция генерирует HTML-код для значков на основе типа предоставленного слоя:
        либо из файла, либо из экземпляра Zabbix.

        :param instance: Параметр instance представляет собой экземпляр класса модели Layers,
         который содержит информацию.
        :return: форматированный HTML-код для значка на основе типа экземпляра слоя,
         переданного в качестве аргумента. Если экземпляр имеет тип "zabbix",
         возвращается значок с заливкой круга указанными цветами. В противном случае, если
         экземпляр представляет собой слой из файла, функция анализирует файл, чтобы определить,
         содержит ли он маркер, многоугольник или линию, и возвращает соответствующий HTML-код с
         отображением нескольких значков.
        """

        if instance.type == "zabbix":
            html = get_icons_html_code(
                instance.points_color,
                instance.points_border_color,
                icon_name="circle-fill",
            )

        else:
            # Слой из файла
            try:
                file_info = self.parse_layer_file(instance.from_file.path)
            except Exception as exc:
                return format_html(f'<div style="color: red">{exc}</div>')

            html = ""
            icon_name = instance.marker_icon_name
            if file_info.get("Point"):
                # Если присутствует маркер в файле
                icon: str = cast(
                    str,
                    get_icons_html_code(
                        instance.points_color,
                        instance.points_border_color,
                        icon_name=icon_name,
                    ),
                )
                html += icon
            if file_info.get("Polygon"):
                # Если присутствует полигон в файле
                colors = file_info["Polygon"]["colours"].most_common(1)
                main_color = colors[0][0] if colors else instance.polygon_fill_color
                html += get_polygon(fill_color=main_color)
            if file_info.get("LineString"):
                # Если присутствует линия в файле
                colors = file_info["LineString"]["colours"].most_common(1)
                main_color = colors[0][0] if colors else instance.polygon_border_color
                html += get_line(fill_color=main_color)

        return format_html(html)  # type: ignore

    @admin.display(description="Тип слоя")
    def layer_type(self, instance: Layers):
        """
        Эта функция возвращает тип слоя в зависимости от того, был ли он создан из файла или группы Zabbix.

        :return: Функция layer_type возвращает строку, описывающую тип экземпляра Layers.
        """
        if instance.from_file:
            return mark_safe(
                f"На основе файла - <strong>\"{instance.from_file.name.rsplit('/', 1)[-1]}\"</strong>"
            )
        if instance.zabbix_group_name:
            return mark_safe(f'На основе группы Zabbix - <strong>"{instance.zabbix_group_name}"</strong>')

        return "Неизвестный тип слоя"

    @staticmethod
    def parse_layer_file(file_path) -> dict:
        """
        ## Функция анализирует файл слоя и возвращает словарь, содержащий информацию о типах и цветах объектов в файле.

        ```python
            {
                'LineString': {
                    'colours': Counter({'#ed4543': 332, '#595959': 138}),
                    'count': 470,
                    'percent': 0.4
                },
                'Point': {
                    'colours': Counter({'#ed4543': 200, '#595959': 67, '#b51eff': 1}),
                    'count': 268,
                    'percent': 0.23
                },
                'Polygon': {
                    'colours': Counter({'#56db40': 233, '#ffd21e': 210, '#f371d1': 2, '#ed4543': 1}),
                    'count': 446,
                    'percent': 0.38
                }
            }
        ```

        :param file_path: Путь к файлу слоя, который содержит географические объекты в формате GeoJSON.
        :return: Функция `parse_layer_file` возвращает словарь, содержащий информацию о типах объектов
         в данном файле слоя, включая количество объектов каждого типа, процентное соотношение каждого
         типа объектов и количество каждого цвета, используемого для каждого типа объектов.
        """

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


@admin.register(Maps)
class MapsAdmin(admin.ModelAdmin):
    readonly_fields = ("map_image",)
    list_display = ("name", "map_layers", "description", "url")
    filter_horizontal = ("users", "layers")
    fieldsets = (
        ("Основные", {"fields": ("name", "map_image", "preview_image", "description")}),
        (
            "Файл карты",
            {"fields": ("from_file",)},
        ),
        (
            "Сторонняя карта по URL",
            {"fields": ("map_url",)},
        ),
        (
            "Укажите слои, из которых будет собрана карта",
            {"fields": ("interactive", "layers")},
        ),
        (
            "Укажите пользователей, которые будут иметь доступ к карте",
            {"fields": ("users",)},
        ),
    )

    @admin.display(description="Открыть")
    def url(self, instance: Maps):
        url = reverse("interactive-map-show", args=[instance.pk])
        return format_html(
            f"""<a href='{url}' target='_blank'><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-box-arrow-right" viewBox="0 0 16 16">
              <path fill-rule="evenodd" d="M10 12.5a.5.5 0 0 1-.5.5h-8a.5.5 0 0 1-.5-.5v-9a.5.5 0 0 1 .5-.5h8a.5.5 0 0 1 .5.5v2a.5.5 0 0 0 1 0v-2A1.5 1.5 0 0 0 9.5 2h-8A1.5 1.5 0 0 0 0 3.5v9A1.5 1.5 0 0 0 1.5 14h8a1.5 1.5 0 0 0 1.5-1.5v-2a.5.5 0 0 0-1 0z"/>
              <path fill-rule="evenodd" d="M15.854 8.354a.5.5 0 0 0 0-.708l-3-3a.5.5 0 0 0-.708.708L14.293 7.5H5.5a.5.5 0 0 0 0 1h8.793l-2.147 2.146a.5.5 0 0 0 .708.708z"/>
            </svg></a>""",
        )

    @staticmethod
    def map_image(instance: Maps):
        return format_html(f"""<img height=300 src="{instance.preview_image.url}" >""")

    @admin.display(description="Структура")
    def map_layers(self, instance: Maps):
        text = ""

        if instance.type == "zabbix":
            text = "<h6>Слои:</h6>"
            for layer in instance.layers.all():
                if layer.type == "zabbix":
                    text += f"""
                    <li style="white-space: nowrap; color: {layer.points_color}">{svg_zabbix_icon} {layer.name}</li>"""
                elif layer.type == "file":
                    text += f"""
                    <li style="white-space: nowrap;"> {svg_file_icon} {layer.name}</li>"""
                else:
                    text += f"""
                    <li style="white-space: nowrap;">{layer}</li>"""

        elif instance.type == "external":
            text = f'<a href="{instance.map_url}" target="_blank">URL</a>'

        elif instance.type == "file":
            text = f"""
            <p style="white-space: nowrap;">{svg_file_icon} {instance.from_file.name.rsplit('/', 1)[-1]}</p>
            """

        return format_html(text)
