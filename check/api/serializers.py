from re import findall

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from ..models import Devices, InterfacesComments, DeviceMedia, UsersActions


class DevicesSerializer(serializers.ModelSerializer):
    """
    ## Класс сериализатора модели Devices
    """

    group = serializers.CharField(source="group.name")

    class Meta:
        model = Devices
        fields = ["ip", "name", "vendor", "group", "model", "port_scan_protocol"]


class DeviceMediaSerializer(serializers.ModelSerializer):
    url = serializers.URLField(source="file.url", read_only=True)
    name = serializers.CharField(source="file_name", read_only=True)
    is_image = serializers.BooleanField(read_only=True)
    file = serializers.FileField(write_only=True)

    class Meta:
        model = DeviceMedia
        fields = [
            "id",
            "file",
            "name",
            "file_type",
            "is_image",
            "description",
            "mod_time",
            "url",
        ]
        read_only_fields = ["id", "mod_time", "file_type"]


class InterfacesCommentsSerializer(serializers.ModelSerializer):
    device = serializers.SlugRelatedField(
        slug_field="name",
        help_text="Название оборудования",
        queryset=Devices.objects.all(),
    )

    class Meta:
        model = InterfacesComments
        fields = ["id", "interface", "comment", "user", "device"]
        read_only_fields = ["id", "user"]


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


class RequiredBooleanField(serializers.BooleanField):
    default_empty_html = serializers.empty


class PortControlSerializer(serializers.Serializer):
    """
    ## Cериализатор для изменения статуса порта
    """

    port = serializers.CharField(max_length=50, required=True)
    status = serializers.ChoiceField(choices=["up", "down", "reload"], required=True)
    save = RequiredBooleanField(required=True)  # type: ignore

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

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class UserDeviceActionSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username")

    class Meta:
        model = UsersActions
        fields = ["time", "user", "action"]
