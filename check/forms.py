from re import findall
from django import forms
from django.core.exceptions import ValidationError


class BrassSessionForm(forms.Form):
    mac = forms.CharField(max_length=24, required=True)
    device = forms.CharField(max_length=255, required=True)
    port = forms.CharField(max_length=50, required=True)
    desc = forms.CharField(max_length=255, required=False)
    ajax = forms.BooleanField(required=False)

    def clean_mac(self):
        mac = findall(r"\w", self.cleaned_data["mac"])
        if len(mac) == 12:
            return "".join(mac).lower()
        raise ValidationError("Неверный MAC")


class ADSLProfileForm(forms.Form):
    index = forms.IntegerField(min_value=0)
    port = forms.CharField(max_length=50, required=True)
    device = forms.CharField(max_length=255, required=True)

    def clean_index(self):
        if self.cleaned_data["index"] < 0:
            raise ValidationError("Индекс профиля должен быть больше 0")
        return self.cleaned_data["index"]
