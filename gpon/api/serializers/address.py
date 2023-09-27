import re

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from gpon.models import Address, HouseB


def format_addresses_data(data):
    """
    Функция format_addresses_data принимает словарь data в качестве входных данных и изменяет значения в словаре,
    чтобы они имели регистр заголовков для строк, и преобразует названия определенных улиц в нижний регистр.

    :param data: Параметр data представляет собой словарь, содержащий данные адреса. Он может иметь такие ключи, как
     «улица», «город», «штат» и т. д., где соответствующие значения представляют собой строки,
     представляющие информацию об адресе.
    """
    for key in data:
        if isinstance(data[key], str):
            data[key] = data[key].title()
        if key == "street" and data[key]:
            data[key] = re.sub(
                r"Улица|Проспект|площадь|Проезд|Бульвар|Шоссе|Переулок|Тупик",
                lambda x: x.group(0).lower(),
                data[key],
            )


class AddressSerializer(serializers.ModelSerializer):
    planStructure = serializers.CharField(
        source="plan_structure", required=False, allow_blank=True, max_length=128
    )

    class Meta:
        model = Address
        fields = [
            "region",
            "settlement",
            "planStructure",
            "street",
            "house",
            "block",
            "floor",
            "apartment",
        ]

    @staticmethod
    def validate_region(value: str):
        if len(value) < 5:
            raise ValidationError("Регион должен содержать более 4 символов")
        return value.upper()

    @staticmethod
    def validate_planStructure(value: str):
        if not value:  # Это не обязательное поле
            return value
        return value.upper()

    @staticmethod
    def validate_street(value: str):
        """
        Функция validate_street принимает строковое значение, представляющее название улицы,
        проверяет и форматирует его в соответствии с определенными правилами и возвращает
        отформатированное название улицы в верхнем регистре.
        :return: проверенное и отформатированное название улицы в верхнем регистре.
        """

        if not value:  # Это не обязательное поле
            return value

        value = value.strip()

        # Заменяем сокращение "ул." на полное слово "улица"
        value = re.sub(r"ул\.|ул(?=\s)", "улица", value, flags=re.IGNORECASE)
        value = re.sub(
            r"пр-кт\.|пр-кт(?=\s)|просп\.|просп(?=\s)", "проспект", value, flags=re.IGNORECASE
        )
        value = re.sub(
            r"пр-зд\.|пр-зд(?=\s)|пр-д\.|пр-д(?=\s)", "проезд", value, flags=re.IGNORECASE
        )
        value = re.sub(
            r"б-р\.|б-р(?=\s)|бул[ьвар]*?\.|бул[ьвар]*?(?=\s)",
            "бульвар",
            value,
            flags=re.IGNORECASE,
        )
        value = re.sub(
            r"ш\.|ш(?=\s)|шосе(?=\s)|шос\.|шос(?=\s)", "шоссе", value, flags=re.IGNORECASE
        )
        value = re.sub(
            r"пер\.|пер(?=\s)|п-к\.|п-к(?=\s)|пер-к\.|пер-к(?=\s)",
            "переулок",
            value,
            flags=re.IGNORECASE,
        )
        value = re.sub(r"т\.", "тупик", value, flags=re.IGNORECASE)

        # Добавляем пробел после слова "улица", если его нет
        value = re.sub(
            r"(улица|проспект|площадь|проезд|бульвар|шоссе|переулок|тупик)(\S.+)",
            r"\1 \2",
            value,
            flags=re.IGNORECASE,
        )

        value = re.sub(r"\s+", " ", value, flags=re.IGNORECASE)

        # Но если указано, то проверяем правильность
        if not re.search(
            r"улица|проспект|площадь|проезд|бульвар|шоссе|переулок|тупик", value, re.IGNORECASE
        ):
            raise ValidationError(
                "Укажите полное название с указанием типа"
                " (улица/проспект/площадь/проезд/бульвар/шоссе/переулок/тупик)"
            )

        if len(value) < 10:
            raise ValidationError("Название улицы должно быть длиннее :)")

        return value.upper()

    @staticmethod
    def validate_settlement(value: str):
        if len(value) < 3:
            raise ValidationError("Населенный пункт должен содержать более 4 символов")
        return value.upper()

    @staticmethod
    def validate_house(value: str):
        return value.upper()

    @staticmethod
    def validate(data):
        if not data.get("planStructure") and not data.get("street"):
            raise ValidationError("Необходимо указать либо СНТ ТСН, либо улицу")
        return data

    @staticmethod
    def create(validated_data) -> Address:
        try:
            address = Address.objects.get(**validated_data)
        except Address.DoesNotExist:
            return Address.objects.create(**validated_data)
        return address

    def to_representation(self, instance):
        data = super().to_representation(instance)
        format_addresses_data(data)
        return data


class BuildingAddressSerializer(serializers.ModelSerializer):
    region = serializers.CharField(source="address.region")
    settlement = serializers.CharField(source="address.settlement")
    planStructure = serializers.CharField(source="address.plan_structure")
    street = serializers.CharField(source="address.street")
    house = serializers.CharField(source="address.house")
    block = serializers.CharField(source="address.block")
    building_type = serializers.ChoiceField(
        source="apartment_building", choices=["building", "house"]
    )

    class Meta:
        model = HouseB
        fields = [
            "id",
            "region",
            "settlement",
            "planStructure",
            "street",
            "house",
            "block",
            "building_type",
            "floors",
            "total_entrances",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        format_addresses_data(data)
        data["building_type"] = "building" if instance.apartment_building else "house"
        return data
