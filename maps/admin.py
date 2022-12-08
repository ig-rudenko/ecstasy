from django.contrib import admin
from django import forms
from pyzabbix import ZabbixAPI

from django.utils.html import mark_safe, format_html
from app_settings.models import ZabbixConfig
from maps.models import Layers, Maps


svg_file_icon = """<svg style="vertical-align: middle" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-file-earmark-code" viewBox="0 0 16 16">
  <path d="M14 4.5V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h5.5L14 4.5zm-3 0A1.5 1.5 0 0 1 9.5 3V1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V4.5h-2z"/>
  <path d="M8.646 6.646a.5.5 0 0 1 .708 0l2 2a.5.5 0 0 1 0 .708l-2 2a.5.5 0 0 1-.708-.708L10.293 9 8.646 7.354a.5.5 0 0 1 0-.708zm-1.292 0a.5.5 0 0 0-.708 0l-2 2a.5.5 0 0 0 0 .708l2 2a.5.5 0 0 0 .708-.708L5.707 9l1.647-1.646a.5.5 0 0 0 0-.708z"/>
</svg>"""


def get_icons_html_code(fill_color: str, stroke_color: str, icon_name=None):
    icons = [
        # Circle fill
        {
            "name": "circle-fill",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" class="bi bi-circle-fill" viewBox="0 0 16 16">
                <circle cx="8" cy="8" r="7" stroke="{stroke_color}" />
            </svg>""",
        },
        # Треугольник
        {
            "name": "triangle",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" class="bi bi-triangle-fill" viewBox="0 0 16 17">
              <path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z" stroke="{stroke_color}" />
            </svg>""",
        },
        # Ромб
        {
            "name": "diamond",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" class="bi bi-diamond-fill" viewBox="-1 -1 18 18">
              <path fill-rule="evenodd" d="M6.95.435c.58-.58 1.52-.58 2.1 0l6.515 6.516c.58.58.58 1.519 0 2.098L9.05 15.565c-.58.58-1.519.58-2.098 0L.435 9.05a1.482 1.482 0 0 1 0-2.098L6.95.435z" stroke="{stroke_color}" />
            </svg>""",
        },
        # Record circle
        {
            "name": "record-circle",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" class="bi bi-record-circle" viewBox="0 0 16 16">
              <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
              <path d="M11 8a3 3 0 1 1-6 0 3 3 0 0 1 6 0z" stroke="{stroke_color}" />
            </svg>""",
        },
        # Гаечный ключ регулируемый круг
        {
            "name": "wrench-circle",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" class="bi bi-wrench-adjustable-circle" viewBox="0 0 16 16">
              <path d="M12.496 8a4.491 4.491 0 0 1-1.703 3.526L9.497 8.5l2.959-1.11c.027.2.04.403.04.61Z"/>
              <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0Zm-1 0a7 7 0 1 0-13.202 3.249l1.988-1.657a4.5 4.5 0 0 1 7.537-4.623L7.497 6.5l1 2.5 1.333 3.11c-.56.251-1.18.39-1.833.39a4.49 4.49 0 0 1-1.592-.29L4.747 14.2A7 7 0 0 0 15 8Zm-8.295.139a.25.25 0 0 0-.288-.376l-1.5.5.159.474.808-.27-.595.894a.25.25 0 0 0 .287.376l.808-.27-.595.894a.25.25 0 0 0 .287.376l1.5-.5-.159-.474-.808.27.596-.894a.25.25 0 0 0-.288-.376l-.808.27.596-.894Z"/>
            </svg>""",
        },
        # Круг в треугольнике
        {
            "name": "circle-in-triangle",
            "code": f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="{fill_color}" class="bi bi-diamond-fill" viewBox="0 0 16 16">
              <path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z" stroke="{2}" />
              <circle cx="8" cy="10" r="4" stroke="{stroke_color}" />
            </svg>""",
        },
    ]

    if icon_name is None:
        return ((ico["name"], mark_safe(ico["code"])) for ico in icons)

    else:
        for ico in icons:
            if icon_name == ico["name"]:
                return ico["code"]


def get_zabbix_groups():
    """
    Возвращает список кортежей вида (group_name, group_name) для всех групп в Zabbix
    :return: Список кортежей.
    """
    zbx_settings = ZabbixConfig.load()
    with ZabbixAPI(zbx_settings.url) as zbx:
        # Вход на сервер Zabbix.
        zbx.login(zbx_settings.login, zbx_settings.password)
        # Получение всех групп узлов сети из Zabbix.
        groups = zbx.hostgroup.get(output=["name"])

    choices_groups = ((g["name"], g["name"]) for g in groups)
    return choices_groups


class LayerFrom(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Динамически смотрим группы из Zabbix
        self.fields["zabbix_group_name"] = forms.ChoiceField(
            label="Выберите группу Zabbix", choices=get_zabbix_groups()
        )
        self.fields["marker_icon_name"] = forms.ChoiceField(
            label="Выберите иконку",
            widget=forms.RadioSelect,
            choices=get_icons_html_code(
                self.instance.points_color, self.instance.points_border_color
            ),
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
    list_display = ("layer_name", "icon", "layer_type", "description")
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
    def layer_name(self, instance: Layers):
        if instance.type == "zabbix":
            return instance.name
        if instance.type == "file":
            return format_html(f"{svg_file_icon} {instance.name}")

    @admin.display(description="Иконка")
    def icon(self, instance: Layers):
        if instance.type == "zabbix":
            icon_name = "circle-fill"
        else:
            icon_name = instance.marker_icon_name

        return format_html(
            get_icons_html_code(
                instance.points_color,
                instance.points_border_color,
                icon_name=icon_name,
            )
        )

    @admin.display(description="Тип слоя")
    def layer_type(self, instance: Layers):
        if instance.from_file:
            return mark_safe(
                f"На основе файла - <strong>\"{instance.from_file.name.rsplit('/', 1)[-1]}\"</strong>"
            )
        if instance.zabbix_group_name:
            return mark_safe(
                f'На основе группы Zabbix - <strong>"{instance.zabbix_group_name}"</strong>'
            )


@admin.register(Maps)
class MapsAdmin(admin.ModelAdmin):
    readonly_fields = ("map_image",)
    list_display = ("name", "map_layers", "description")
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

    @staticmethod
    def map_image(instance: Maps):
        return format_html(f"""<img height=300 src="{instance.preview_image.url}" >""")

    @admin.display(description="Слои/URL")
    def map_layers(self, instance: Maps):
        text = ""

        if instance.type == "zabbix":
            text = "<h3>Слои:</h3>"
            for layer in instance.layers.all():
                if layer.type == "zabbix":
                    text += f"""
                    <li style="white-space: nowrap; color: {layer.points_color}" >{layer.name}</li>"""
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
