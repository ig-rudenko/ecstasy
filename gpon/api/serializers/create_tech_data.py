import orjson
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MaxValueValidator, MinValueValidator
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from check.models import Devices
from devicemanager.device import Interfaces
from gpon.models import Address, End3, HouseB, HouseOLTState, OLTState

from .address import AddressSerializer
from .common import End3Serializer


class OLTStateSerializer(serializers.ModelSerializer):
    deviceName = serializers.CharField(source="device.name")
    devicePort = serializers.CharField(source="olt_port")

    class Meta:
        model = OLTState
        fields = ["id", "deviceName", "devicePort", "fiber", "description"]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._device: Devices | None = None

    def validate_deviceName(self, value: str) -> str:
        """
        Функция validate_deviceName проверяет, существует ли устройство с данным именем в базе данных, и выдает ошибку
        проверки, если его нет.

        :param value: Параметр value представляет имя устройства, которое необходимо проверить
        :return: значение параметра `value`.
        """
        try:
            self._device = Devices.objects.get(name=value)
        except Devices.DoesNotExist as exc:
            raise ValidationError(f"Оборудование `{value}` не существует") from exc
        return value

    def validate_devicePort(self, value: str) -> str:
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
            interfaces = Interfaces(orjson.loads(self._device.devicesinfo.interfaces or "[]"))
        except ObjectDoesNotExist as exc:
            raise ValidationError(
                "Данное оборудование не имеет портов для проверки, пожалуйста, откройте его, чтобы опросить"
            ) from exc
        else:
            for intf in interfaces:
                if intf.name == value:
                    return value

        raise ValidationError(f"Данное оборудование не имеет порта `{value}`")

    @staticmethod
    def create(validated_data) -> OLTState:
        device: Devices = Devices.objects.get(name=validated_data["device"]["name"])

        instance, _ = OLTState.objects.update_or_create(
            device=device,
            olt_port=validated_data["olt_port"],
            defaults={
                "fiber": validated_data.get("fiber"),
                "description": validated_data.get("description"),
            },
        )

        return instance


class WriteOnlyHouseBAddressSerializer(AddressSerializer):
    building_type = serializers.ChoiceField(choices=["building", "house"], required=True, write_only=True)
    floors = serializers.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        required=True,
        write_only=True,
    )
    total_entrances = serializers.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(255)],
        required=True,
        write_only=True,
    )
    planStructure = serializers.CharField(
        source="plan_structure", required=False, allow_blank=True, max_length=128
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


class CreateHouseOLTStateSerializer(serializers.ModelSerializer):
    address = WriteOnlyHouseBAddressSerializer(source="house.address", write_only=True)

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


class End3WriterSerializer(End3Serializer):
    id = serializers.IntegerField()


class End3CreateListSerializer(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=["splitter", "rizer"],
        error_messages={"invalid_choice": "Абонентская линия должна быть либо splitter, либо rizer."},
    )
    existingSplitter = End3WriterSerializer(required=False, allow_null=True)
    portCount = serializers.ChoiceField(
        choices=[2, 4, 8, 16, 24],
        error_messages={
            "invalid_choice": "Кол-во портов на splitter, либо волокон на rizer должны быть (2, 4, 8, 16, 24)"
        },
    )
    list = End3CreateSerializer(many=True, required=False, allow_null=True)

    @staticmethod
    def validate(data):
        if not data.get("list") and not data.get("existingSplitter"):
            raise ValidationError("Необходимо выбрать хотя бы один splitter/rizer")
        return data

    def validate_existingSplitter(self, value):
        if value is None:
            return value
        if not value.get("id"):
            raise ValidationError("Не был передан `id` существующего сплиттера")
        try:
            End3.objects.get(id=value["id"])
        except End3.DoesNotExist as exc:
            raise ValidationError(f"Сплиттер с id={value['id']} не существует") from exc
        return value


class CreateTechDataSerializer(serializers.Serializer):
    oltState = OLTStateSerializer(
        error_messages={"required": "Обязательный параметр для данных OLT состояния"}
    )
    houseB = CreateHouseOLTStateSerializer(
        error_messages={"required": "Обязательный параметр для данных строения"}
    )
    end3 = End3CreateListSerializer(
        error_messages={"required": "Обязательный параметр для данных splitter/rizer"}
    )

    class Meta:
        fields = ["oltState", "houseB", "end3"]

    def create(self, validated_data) -> OLTState:
        """
        Функция создает объект OLTState и связывает его с объектом HouseOLTState,
        а также создает несколько объектов End3 и связывает их с объектом HouseOLTState.

        :return: экземпляр класса OLState.
        """
        olt_state = OLTStateSerializer.create(validated_data["oltState"])

        house_olt_state = CreateHouseOLTStateSerializer.create(validated_data["houseB"])
        house_olt_state.statement = olt_state
        house_olt_state.save(update_fields=["statement"])

        if validated_data["end3"].get("existingSplitter"):
            # Если был выбран уже существующий сплиттер
            end3_obj_list = [self.get_exiting_splitter(validated_data)]

        else:  # Создаем НОВЫЕ splitter/rizer
            end3_obj_list = self.create_new_end3(validated_data, house_olt_state)

        house_olt_state.end3_set.add(*end3_obj_list)
        return olt_state

    @staticmethod
    def get_exiting_splitter(validated_data) -> End3:
        try:
            splitter_id = validated_data["end3"]["existingSplitter"]["id"]
            return End3.objects.get(id=splitter_id)
        except End3.DoesNotExist as exc:
            raise ValidationError("Выбранный вами сплиттер не существует.") from exc

    @staticmethod
    def create_new_end3(validated_data, house_olt_state: HouseOLTState) -> list[End3]:
        # Создаем НОВЫЕ splitter/rizer
        end3_obj_list = []
        for end3_unit in validated_data["end3"].get("list", []):
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
        return end3_obj_list


class AddEnd3ToHouseOLTStateSerializer(serializers.Serializer):
    end3 = End3CreateListSerializer(
        error_messages={"required": "Обязательный параметр для данных splitter/rizer"}
    )

    houseOltStateID = serializers.PrimaryKeyRelatedField(queryset=HouseOLTState.objects)

    class Meta:
        fields = ["end3", "houseOltStateID"]

    def create(self, validated_data: dict) -> list[End3]:
        house_olt_state: HouseOLTState = validated_data["houseOltStateID"]
        end3 = CreateTechDataSerializer.create_new_end3(validated_data, house_olt_state)
        house_olt_state.end3_set.add(*end3)
        return end3
