import re
from typing import Optional

import orjson
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinValueValidator, MaxValueValidator
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from check.models import Devices
from ..models import Address, OLTState, HouseOLTState, HouseB, End3


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
        for key in data:
            if isinstance(data[key], str):
                data[key] = data[key].title()
            if key == "street":
                data[key] = re.sub(
                    r"Улица|Проспект|площадь|Проезд|Бульвар|Шоссе|Переулок|Тупик",
                    lambda x: x.group(0).lower(),
                    data[key],
                )
        return data


class OLTStateSerializer(serializers.ModelSerializer):
    deviceName = serializers.CharField(source="device.name")
    devicePort = serializers.CharField(source="olt_port")

    class Meta:
        model = OLTState
        fields = ["deviceName", "devicePort", "fiber", "description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._device: Optional[Devices] = None

    def validate_deviceName(self, value):
        """
        Функция validate_deviceName проверяет, существует ли устройство с данным именем в базе данных, и выдает ошибку
        проверки, если его нет.

        :param value: Параметр value представляет имя устройства, которое необходимо проверить
        :return: значение параметра `value`.
        """
        try:
            self._device: Devices = Devices.objects.get(name=value)
        except Devices.DoesNotExist:
            raise ValidationError(f"Оборудование `{value}` не существует")
        return value

    def validate_devicePort(self, value):
        """
        Функция validate_devicePort проверяет, имеет ли данное устройство определенный порт,
        и выдает ошибку проверки, если это не так.

        :param value: Параметр value представляет порт устройства, который необходимо проверить
        :return: Если `self._device` имеет значение None, то `value` возвращается как есть. В противном случае, если
         «интерфейс» соответствует любому из интерфейсов в «self._device.devicesinfo.interfaces»,
         то возвращается его значение. Если ни один из интерфейсов не соответствует значению,
         то возникает ошибка ValidationError
        """
        if self._device is None:
            return value
        try:
            interfaces = orjson.loads(self._device.devicesinfo.interfaces or "[]")
        except ObjectDoesNotExist:
            raise ValidationError(
                "Данное оборудование не имеет портов для проверки, "
                "пожалуйста, откройте его, чтобы опросить"
            )
        else:
            for intf in interfaces:
                if intf["Interface"] == value:
                    return value

        raise ValidationError(f"Данное оборудование не имеет порта `{value}`")

    @staticmethod
    def create(validated_data) -> OLTState:
        device: Devices = Devices.objects.get(name=validated_data["device"]["name"])

        instance = OLTState.objects.create(
            device=device,
            olt_port=validated_data["olt_port"],
            fiber=validated_data.get("fiber"),
            description=validated_data.get("description"),
        )

        return instance


class HouseBAddressSerializer(AddressSerializer):
    building_type = serializers.ChoiceField(
        choices=["building", "house"], required=True, write_only=True
    )
    floors = serializers.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)], required=True, write_only=True
    )
    total_entrances = serializers.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(255)], required=True, write_only=True
    )

    class Meta:
        model = Address
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


class HouseOLTStateSerializer(serializers.ModelSerializer):
    address = HouseBAddressSerializer(source="house.address")

    class Meta:
        model = HouseOLTState
        fields = ["address", "entrances", "description"]

    @staticmethod
    def create(validated_data) -> HouseOLTState:
        building_type = validated_data["house"]["address"]["building_type"]
        floors = validated_data["house"]["address"]["floors"]
        total_entrances = validated_data["house"]["address"]["total_entrances"]

        address = AddressSerializer.create(
            {
                "region": validated_data["house"]["address"]["region"],
                "settlement": validated_data["house"]["address"]["settlement"],
                "plan_structure": validated_data["house"]["address"].get("plan_structure"),
                "street": validated_data["house"]["address"].get("street"),
                "house": validated_data["house"]["address"]["house"],
                "block": validated_data["house"]["address"].get("block"),
                "floor": validated_data["house"]["address"].get("floor"),
                "apartment": validated_data["house"]["address"].get("apartment"),
            }
        )

        house, _ = HouseB.objects.update_or_create(
            address=address,
            defaults={
                "apartment_building": building_type == "building",
                "floors": floors,
                "total_entrances": total_entrances,
            },
        )

        house_olt_state = HouseOLTState.objects.create(
            house=house,
            description=validated_data["description"],
            entrances=validated_data["entrances"],
        )
        return house_olt_state


class End3CreateSerializer(serializers.Serializer):
    address = AddressSerializer(required=False, allow_null=True)
    buildAddress = serializers.BooleanField()
    location = serializers.CharField(max_length=255)


class End3CreateListSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["splitter", "rizer"])
    existingSplitter = serializers.IntegerField(required=False, allow_null=True)
    portCount = serializers.ChoiceField(choices=[2, 4, 8, 16, 24])
    list = End3CreateSerializer(many=True)


class CreateTechDataSerializer(serializers.Serializer):
    oltState = OLTStateSerializer()
    houseB = HouseOLTStateSerializer()
    end3 = End3CreateListSerializer()

    class Meta:
        fields = ["oltState", "houseB", "end3"]

    def create(self, validated_data) -> OLTState:
        """
        Функция создает объект OLTState и связывает его с объектом HouseOLTState,
        а также создает несколько объектов End3 и связывает их с объектом HouseOLTState.

        :return: экземпляр класса OLState.
        """
        olt_state = OLTStateSerializer.create(validated_data["oltState"])

        house_olt_state = HouseOLTStateSerializer.create(validated_data["houseB"])
        house_olt_state.statement = olt_state
        house_olt_state.save(update_fields=["statement"])

        end3_obj_list = []
        # Создаем splitter/rizer
        for end3_unit in validated_data["end3"]["list"]:
            if end3_unit["buildAddress"]:
                # Если адрес сплиттера/райзера такой же как и у дома
                end3_unit_address = house_olt_state.house.address
            else:
                end3_unit_address = AddressSerializer.create(end3_unit["address"])

            end3_obj_list.append(
                End3.objects.create(
                    type=validated_data["end3"]["type"],
                    capacity=validated_data["end3"]["portCount"],
                    location=end3_unit["location"],
                    address=end3_unit_address,
                )
            )

        house_olt_state.end3_set.add(*end3_obj_list)
        return olt_state


# ================= Для просмотра ===================


class End3ListSerializer(serializers.ModelSerializer):
    address = AddressSerializer(read_only=True)

    class Meta:
        model = End3
        fields = ["id", "address", "location", "type", "capacity"]


class ListHouseOLTStateSerializer(HouseOLTStateSerializer):
    end3 = End3ListSerializer(many=True, source="house.end3_set", read_only=True)

    class Meta:
        model = HouseOLTState
        fields = ["address", "entrances", "description", "end3"]


class ListTechDataSerializer(serializers.ModelSerializer):
    deviceName = serializers.CharField(source="house_olt_state.device.name", read_only=True)
    devicePort = serializers.CharField(source="house_olt_state.olt_port", read_only=True)
    fiber = serializers.CharField(source="house_olt_state.fiber", read_only=True)
    description = serializers.CharField(source="house_olt_state.description", read_only=True)

    class Meta:
        model = HouseB
        fields = ["deviceName", "devicePort", "fiber", "description"]

    def to_representation(self, instance: HouseB):
        data = super().to_representation(instance)
        data["entrances"] = instance.olt_states.all()
        return data
