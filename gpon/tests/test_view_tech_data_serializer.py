import json

from django.test import TestCase

from check.models import DeviceGroup, Devices, AuthGroup
from gpon.api.serializers.create_tech_data import CreateTechDataSerializer
from gpon.api.serializers.view_tech_data import ViewOLTStatesTechDataSerializer
from net_tools.models import DevicesInfo
from .data import CREATE_TECH_DATA
from ..models import OLTState


class TestViewOLTStatesTechDataSerializer(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        device = Devices.objects.create(
            auth_group=AuthGroup.objects.create(name="test", login="login", password="password"),
            group=DeviceGroup.objects.create(name="test"),
            ip="10.10.10.10",
            name="device1",
        )
        DevicesInfo.objects.create(
            dev=device,
            interfaces=json.dumps(
                [
                    {"Interface": "0/1/1"},
                    {"Interface": "0/1/2"},
                    {"Interface": "0/1/3"},
                ]
            ),
        )
        serializer = CreateTechDataSerializer(data=CREATE_TECH_DATA)
        serializer.is_valid()
        serializer.create(serializer.validated_data)

    def test_serializer(self):
        serializer = ViewOLTStatesTechDataSerializer(instance=OLTState.objects.all(), many=True)
        print(serializer.data)
