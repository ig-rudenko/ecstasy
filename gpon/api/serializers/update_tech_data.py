import copy

from django.db.models import QuerySet
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from check.models import Devices
from gpon.api.serializers.address import AddressSerializer
from gpon.api.serializers.common import End3Serializer
from gpon.api.serializers.create_tech_data import (
    OLTStateSerializer,
    WriteOnlyHouseBAddressSerializer,
)
from gpon.api.serializers.view_tech_data import TechCapabilitySerializer
from gpon.models import OLTState, HouseOLTState, End3, TechCapability


class UpdateRetrieveOLTStateSerializer(OLTStateSerializer):
    deviceName = serializers.CharField(source="device.name")
    devicePort = serializers.CharField(source="olt_port")

    class Meta:
        model = OLTState
        fields = ["deviceName", "devicePort", "fiber", "description"]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._device: Devices | None = None

    def update(self, instance: OLTState, validated_data) -> OLTState:
        """
        Функция обновляет атрибуты экземпляра OLState с использованием предоставленных проверенных данных и возвращает
        обновленный экземпляр.

        :param instance: Параметр экземпляра является экземпляром класса модели OLTState.
         Он представляет текущее состояние устройства OLT (терминала оптической линии)
        :type instance: OLTState
        :param validated_data: Параметр validated_data — это словарь, содержащий проверенные данные,
         которые передаются в метод update. Он используется для обновления полей объекта экземпляра
        :return: Метод возвращает обновленный экземпляр модели OLState.
        """
        if self._device is None:
            raise ValidationError("Невозможно обновить запись с отсутствующим device id")
        instance.device_id = self._device.id

        if validated_data.get("olt_port") and instance.olt_port != validated_data["olt_port"]:
            # Проверяем, что новый указанный порт еще не занят
            self._validate_port_availability(validated_data)
            instance.olt_port = validated_data["olt_port"]

        if validated_data.get("fiber"):
            instance.fiber = validated_data["fiber"]

        if validated_data.get("description"):
            instance.description = validated_data["description"]

        instance.save()
        return instance

    @staticmethod
    def _validate_port_availability(attrs):
        """Функция проверяет занят ли уже определенный порт на устройстве."""
        try:
            OLTState.objects.get(device__name=attrs["device"]["name"], olt_port=attrs["olt_port"])
        except OLTState.DoesNotExist:
            pass
        else:
            raise ValidationError("Данный порт на оборудовании уже занят")


class UpdateHouseOLTStateSerializer(serializers.ModelSerializer):
    address = WriteOnlyHouseBAddressSerializer(source="house.address")

    class Meta:
        model = HouseOLTState
        fields = ["entrances", "description", "address"]

    def update(self, instance: HouseOLTState, validated_data) -> HouseOLTState:
        data = copy.deepcopy(validated_data)
        building_type = data["house"]["address"].pop("building_type")
        floors = data["house"]["address"].pop("floors")
        total_entrances = data["house"]["address"].pop("total_entrances")

        address = AddressSerializer.create(data["house"]["address"])

        instance.house.address = address
        instance.house.apartment_building = building_type == "building"
        instance.house.total_entrances = total_entrances
        instance.house.floors = floors
        instance.house.save()

        instance.description = validated_data["description"]
        instance.entrances = validated_data["entrances"]
        instance.save()

        return instance


class End3TechCapabilitySerializer(End3Serializer):
    capability = TechCapabilitySerializer(source="techcapability_set", many=True, read_only=True)
    address = AddressSerializer()

    class Meta:
        model = End3
        fields = ["id", "address", "capacity", "location", "type", "capability"]
        read_only_fields = ["id", "type", "capability"]

    def validate_capacity(self, value: int):
        self.instance: End3
        if value < self.instance.capacity:
            tech_capability = self.instance.techcapability_set.all().order_by("number")
            self._get_affected_tech_capability(value, tech_capability)
        return value

    def update(self, instance: End3, validated_data):
        if validated_data.get("capacity"):
            tech_cap_queryset: QuerySet[TechCapability] = self.instance.techcapability_set.all().order_by(
                "number"
            )

            if validated_data["capacity"] < instance.capacity:
                to_delete = self._get_affected_tech_capability(validated_data["capacity"], tech_cap_queryset)
                for tech in to_delete:
                    tech.delete()

            if validated_data["capacity"] > instance.capacity:
                last_tech_cap = tech_cap_queryset.values("number").last()
                last_number = last_tech_cap["number"] if last_tech_cap else 0

                additional_capacity = validated_data["capacity"] - instance.capacity
                for i in range(
                    last_number + 1,
                    last_number + additional_capacity + 1,
                ):
                    TechCapability.objects.create(end3=instance, number=i)

        update_fields = []
        for key, value in validated_data.items():
            if key == "address":
                value = AddressSerializer.create(validated_data["address"])
            setattr(instance, key, value)
            update_fields.append(key)

        instance.save(update_fields=update_fields)

        return instance

    @staticmethod
    def _get_affected_tech_capability(
        new_capacity: int, tech_capabilities: QuerySet[TechCapability]
    ) -> list[TechCapability]:
        """
        Возвращает список объектов `TechCapability`, которые необходимо удалить, на
        основе нового значения ёмкости и списка существующих объектов `TechCapability`.
        Если будут затронуты абонентские подключения, то произойдет ошибка `ValidationError`.

        :param new_capacity: Параметр new_capacity — это целое число, которое представляет новое значение емкости.
         Он используется для определения того, какие объекты TechCapability следует удалить из списка tech_capability.
        :param tech_capabilities: QuerySet объектов типа TechCapability.
        :return: Список объектов TechCapability, которые необходимо удалить.
        """
        to_delete: list[TechCapability] = []
        for i, line in enumerate(tech_capabilities, 1):
            if i <= new_capacity:
                continue
            if line.subscriber_connection.count():
                raise ValidationError("Нельзя, есть абоненты")
            to_delete.append(line)
        return to_delete
