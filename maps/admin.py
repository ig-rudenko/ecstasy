from django.contrib import admin
from django import forms
from pyzabbix import ZabbixAPI

from django.utils.html import mark_safe, format_html
from app_settings.models import ZabbixConfig
from maps.models import Layers, Maps


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
        }


@admin.register(Layers)
class LayersAdmin(admin.ModelAdmin):
    list_display = ("layer_name", "layer_type", "description")
    form = LayerFrom

    fieldsets = (
        ("Описание", {"fields": ("name", "description")}),
        ("Из файла", {"fields": ("from_file",)}),
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
        return mark_safe(
            f"""<span style="color: {instance.points_color}">{instance.name}</span>"""
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
    list_display = ("name", "map_layers", "description")
    filter_horizontal = ("users", "layers")
    fieldsets = (
        ("Основные", {"fields": ("name", "description")}),
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

    @admin.display(description="Слои/URL")
    def map_layers(self, instance: Maps):
        text = ""
        for layer in instance.layers.all():
            text += f"""
            <li style="color: {layer.points_color}" >{layer}</li>
            """

        if not text:
            text = f"<a href=\"{instance.map_url}\" target=\"_blank\">{instance.map_url}</a>"

        return format_html(text)
