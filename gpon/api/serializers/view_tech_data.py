from typing import List

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from gpon.models import OLTState, HouseOLTState, TechCapability, SubscriberConnection, HouseB, End3
from .address import BuildingAddressSerializer, AddressSerializer
from .common import End3Serializer
from .create_tech_data import OLTStateSerializer


class StructuresHouseOLTStateSerializer(serializers.ModelSerializer):
    address = BuildingAddressSerializer(source="house")
    customerLines = End3Serializer(source="end3_set", many=True)

    class Meta:
        model = HouseOLTState
        fields = ["id", "address", "entrances", "description", "customerLines"]


class ViewOLTStatesTechDataSerializer(serializers.ModelSerializer):
    deviceName = serializers.CharField(source="device.name")
    devicePort = serializers.CharField(source="olt_port")
    structures = StructuresHouseOLTStateSerializer(source="house_olt_states", many=True)

    class Meta:
        model = OLTState
        fields = ["id", "deviceName", "devicePort", "fiber", "description", "structures"]


class HouseOLTStateSerializer(serializers.ModelSerializer):
    statement = OLTStateSerializer()
    customerLines = End3Serializer(source="end3_set", many=True)

    class Meta:
        model = HouseOLTState
        fields = ["id", "entrances", "description", "customerLines", "statement"]


class ViewHouseBTechDataSerializer(BuildingAddressSerializer):
    oltStates = HouseOLTStateSerializer(source="house_olt_states", many=True)

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
            "apartment_building",
            "floors",
            "total_entrances",
            "oltStates",
        ]


class SubscriberConnectionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="customer.full_name")

    class Meta:
        model = SubscriberConnection
        fields = ["id", "name", "transit"]


class TechCapabilitySerializer(serializers.ModelSerializer):
    subscribers = SubscriberConnectionSerializer(source="subscriber_connection", many=True, read_only=True)

    class Meta:
        model = TechCapability
        fields = ["id", "status", "number", "subscribers"]
        read_only_fields = ["id", "number", "subscribers"]


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
            tech_capability = self.instance.techcapability_set.all().order_by("number")
            if validated_data["capacity"] < instance.capacity:
                to_delete = self._get_affected_tech_capability(
                    validated_data["capacity"], tech_capability
                )
                for tech in to_delete:
                    tech.delete()

            if validated_data["capacity"] > instance.capacity:
                last_tech_capacity: TechCapability = tech_capability.last()
                additional_capacity = validated_data["capacity"] - instance.capacity
                for i in range(
                    last_tech_capacity.number + 1,
                    last_tech_capacity.number + additional_capacity + 1,
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
    def _get_affected_tech_capability(new_capacity: int, tech_capability) -> List[TechCapability]:
        """
        Функция _get_affected_tech_capability возвращает список объектов TechCapability, которые необходимо удалить, на
        основе нового значения ёмкости и списка существующих объектов TechCapability.

        :param new_capacity: Параметр new_capacity — это целое число, которое представляет новое значение емкости.
         Он используется для определения того, какие объекты TechCapability следует удалить из списка tech_capability
        :param tech_capability: Параметр tech_capability представляет собой список объектов типа TechCapability
        :return: список объектов TechCapability, которые необходимо удалить.
        """
        to_delete = []
        for i, line in enumerate(tech_capability, 1):
            if i <= new_capacity:
                continue
            line: TechCapability
            if line.subscriber_connection.count():
                raise ValidationError("Нельзя, есть абоненты")
            to_delete.append(line)
        return to_delete
