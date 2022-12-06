from django.contrib import admin
from django import forms
from pyzabbix import ZabbixAPI

from django.utils.html import mark_safe, format_html
from app_settings.models import ZabbixConfig
from maps.models import Layers, Maps


svg_file_icon = """<svg style="vertical-align: sub" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-file-earmark-code" viewBox="0 0 16 16">
  <path d="M14 4.5V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h5.5L14 4.5zm-3 0A1.5 1.5 0 0 1 9.5 3V1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V4.5h-2z"/>
  <path d="M8.646 6.646a.5.5 0 0 1 .708 0l2 2a.5.5 0 0 1 0 .708l-2 2a.5.5 0 0 1-.708-.708L10.293 9 8.646 7.354a.5.5 0 0 1 0-.708zm-1.292 0a.5.5 0 0 0-.708 0l-2 2a.5.5 0 0 0 0 .708l2 2a.5.5 0 0 0 .708-.708L5.707 9l1.647-1.646a.5.5 0 0 0 0-.708z"/>
</svg>"""


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
            choices=get_zabbix_groups()
        )

    class Meta:
        model = Layers
        fields = "__all__"
        widgets = {
            "points_color": forms.TextInput(attrs={"type": "color"}),
            "points_border_color": forms.TextInput(attrs={"type": "color"}),
            "default_geojson_opacity": forms.TextInput(),
            "default_geojson_fill_color": forms.TextInput(attrs={"type": "color"}),
            "default_geojson_border_color": forms.TextInput(attrs={"type": "color"}),
        }


@admin.register(Layers)
class LayersAdmin(admin.ModelAdmin):
    list_display = ("layer_name", "layer_type", "description")
    form = LayerFrom

    fieldsets = (
        ("Описание", {"fields": ("name", "description")}),
        (
            "Из файла",
            {
                "fields": (
                    "from_file",
                    "default_geojson_opacity",
                    "default_geojson_fill_color",
                    "default_geojson_border_color",
                ),
            },
        ),
        (
            "Из Zabbix",
            {
                "fields": (
                    "zabbix_group_name",
                    "points_color",
                    "points_border_color",
                    "points_radius",
                )
            },
        ),
    )

    @admin.display(description="Название слоя")
    def layer_name(self, instance: Layers):
        if instance.type == "zabbix":
            return format_html(
                f"""<span style="color: {instance.points_color}">{instance.name}</span>"""
            )
        if instance.type == "file":
            return format_html(
                f"{svg_file_icon} {instance.name}"
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
            for layer in instance.layers.all():
                text += f"""
                <li style="color: {layer.points_color}" >{layer}</li>
                """

        elif instance.type == "external":
            text = (
                f'<a href="{instance.map_url}" target="_blank">{instance.map_url}</a>'
            )

        elif instance.type == "file":
            text = f"{svg_file_icon} {instance.from_file.name.rsplit('/', 1)[-1]}"

        return format_html(text)
