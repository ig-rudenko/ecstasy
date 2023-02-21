from django import forms
from django.core.exceptions import ValidationError
from ecstasy_project.settings import django_actions_logger


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
    device_name = forms.CharField(max_length=255, required=True)

    def clean_index(self):
        django_actions_logger.info(self.cleaned_data)
        if self.cleaned_data["index"] < 0:
            raise ValidationError("Индекс профиля должен быть больше 0")
        return self.cleaned_data["index"]
