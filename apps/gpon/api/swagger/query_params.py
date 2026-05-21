from rest_framework import serializers


class BuildingAddressesQueryParamsSwaggerSerializer(serializers.Serializer):
    device = serializers.CharField(required=False)
    port = serializers.CharField(required=False)
    search = serializers.CharField(required=False)


class End3AddressesQueryParamsSwaggerSerializer(serializers.Serializer):
    address_id = serializers.IntegerField(required=False, min_value=1)
    search = serializers.CharField(required=False)


class SubscribersOnDevicePortQueryParamsSwaggerSerializer(serializers.Serializer):
    port = serializers.CharField(required=True)
    ont_id = serializers.IntegerField(required=False, min_value=0, default=0)


class DevicePortQueryParamsSwaggerSerializer(serializers.Serializer):
    port = serializers.CharField(required=True)


class SearchPaginationQueryParamsSwaggerSerializer(serializers.Serializer):
    search = serializers.CharField(required=False)


class TechDataListQueryParamsSwaggerSerializer(serializers.Serializer):
    region = serializers.CharField(required=False)
    settlement = serializers.CharField(required=False)
    planStructure = serializers.CharField(required=False)
    street = serializers.CharField(required=False)
    house = serializers.CharField(required=False)
    block = serializers.CharField(required=False)
    deviceName = serializers.CharField(required=False)
    devicePort = serializers.CharField(required=False)
