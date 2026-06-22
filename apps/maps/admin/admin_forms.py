from django import forms
from unfold.widgets import (
    UnfoldAdminColorInputWidget,
    UnfoldAdminRadioSelectWidget,
    UnfoldAdminSelectWidget,
    UnfoldAdminTextInputWidget,
)

from ..models import Layers
from .admin_utils import get_icons_html_code, get_zabbix_groups


class LayerFrom(forms.ModelForm):
    """Form for Layers admin with dynamic zabbix group and marker icons."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["zabbix_group_name"] = forms.ChoiceField(
            label="Выберите группу Zabbix",
            choices=(("", "---------"), *tuple(get_zabbix_groups())),
            required=False,
            widget=UnfoldAdminSelectWidget,  # noqa
        )
        icons = get_icons_html_code(self.instance.points_color, self.instance.points_border_color)
        self.fields["marker_icon_name"] = forms.ChoiceField(
            label="Выберите иконку",
            widget=UnfoldAdminRadioSelectWidget,  # noqa
            choices=icons,  # noqa
            initial=icons[0],
        )

    class Meta:
        model = Layers
        fields = "__all__"
        widgets = {
            "points_color": UnfoldAdminColorInputWidget(attrs={"type": "color"}),
            "points_border_color": UnfoldAdminColorInputWidget(attrs={"type": "color"}),
            "polygon_opacity": UnfoldAdminTextInputWidget(),
            "polygon_fill_color": UnfoldAdminColorInputWidget(attrs={"type": "color"}),
            "polygon_border_color": UnfoldAdminColorInputWidget(attrs={"type": "color"}),
        }
