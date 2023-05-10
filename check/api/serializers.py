from re import findall

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from ..models import Devices, InterfacesComments


class DevicesSerializer(serializers.ModelSerializer):
    """
    ## Класс сериализатора модели Devices
    """

    group = serializers.CharField(source="group.name")

    class Meta:
        model = Devices
        fields = ["ip", "name", "vendor", "group", "model", "port_scan_protocol"]


class InterfacesCommentsSerializer(serializers.ModelSerializer):
    device = serializers.CharField(source="device.name", read_only=True)

    class Meta:
        model = InterfacesComments
        fields = ["id", "interface", "comment", "user", "device"]
        read_only_fields = ["id", "user", "device"]


class MacSerializer(serializers.Serializer):
    mac = serializers.CharField(max_length=24, required=True)

    def validate_mac(self, value):
        """
        ## Удаляет все нешестнадцатеричные символы из строки MAC адреса

        Возвращает MAC в виде строки - `001122334455`.
        """
        mac = findall(r"\w", value)
        if len(mac) == 12:
            return "".join(mac).lower()
        raise ValidationError("Неверный MAC")

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BrassSessionSerializer(MacSerializer):
    """
    ## Проверка правильности ввода данных для работы с пользовательскими сессиями BRAS

    Требуемые поля:
     - str:`mac` - max:24
     - str:`device` - max:255
     - str:`port` - max:50
    """

    device = serializers.CharField(max_length=255, required=True)
    port = serializers.CharField(max_length=50, required=True)


class ADSLProfileSerializer(serializers.Serializer):
    """
    ## Проверка правильности ввода данных для смены xDSL профиля на оборудовании

    Требуемые поля:
     - int:`index` >= 0
     - str:`port` - max:50
    """

    index = serializers.IntegerField(min_value=0)
    port = serializers.CharField(max_length=50, required=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class PortControlSerializer(serializers.Serializer):
    """
    ## Cериализатор для изменения статуса порта
    """

    port = serializers.CharField(max_length=50, required=True)
    status = serializers.ChoiceField(choices=["up", "down", "reload"], required=True)
    save = serializers.BooleanField(required=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class PoEPortStatusSerializer(serializers.Serializer):
    port = serializers.CharField(max_length=50, required=True)
    status = serializers.ChoiceField(choices=["auto-on", "forced-on", "off"], required=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ConfigFileSerializer(serializers.Serializer):
    name = serializers.CharField()
    size = serializers.IntegerField()
    modTime = serializers.CharField()
    isDir = serializers.BooleanField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
