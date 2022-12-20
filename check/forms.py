from re import findall
from django import forms
from django.core.exceptions import ValidationError


class BrassSessionForm(forms.Form):
    """
    ## Форма проверки правильности ввода данных для работы с пользовательскими сессиями BRAS

    Требуемые поля:
     - str:`mac` - max:24
     - str:`device` - max:255
     - str:`port` - max:50

    Опциональные поля:
     - str:`desc` - max:255
     - bool:`ajax`
    """

    mac = forms.CharField(max_length=24, required=True)
    device = forms.CharField(max_length=255, required=True)
    port = forms.CharField(max_length=50, required=True)
    desc = forms.CharField(max_length=255, required=False)
    ajax = forms.BooleanField(required=False)

    def clean_mac(self):
        """
        ## Удаляет все нешестнадцатеричные символы из строки MAC адреса

        Возвращает MAC в виде строки - `001122334455`.
        """
        mac = findall(r"\w", self.cleaned_data["mac"])
        if len(mac) == 12:
            return "".join(mac).lower()
        raise ValidationError("Неверный MAC")


class ADSLProfileForm(forms.Form):
    """
    ## Форма проверки правильности ввода данных для смены xDSL профиля на оборудовании

    Требуемые поля:
     - int:`index` >= 0
     - str:`port` - max:50
     - str:`device` - max:255
    """

    index = forms.IntegerField(min_value=0)
    port = forms.CharField(max_length=50, required=True)
    device = forms.CharField(max_length=255, required=True)

    def clean_index(self):
        if self.cleaned_data["index"] < 0:
            raise ValidationError("Индекс профиля должен быть больше 0")
        return self.cleaned_data["index"]
