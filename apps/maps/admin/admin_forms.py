from django import forms

from ..models import Layers
from .admin_utils import get_icons_html_code, get_zabbix_groups


class LayerFrom(forms.ModelForm):
    """Form for Layers admin with dynamic zabbix group and marker icons."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
