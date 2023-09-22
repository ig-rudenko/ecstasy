import json

from django.test import TestCase
from rest_framework.exceptions import ErrorDetail

from check.models import Devices, AuthGroup, DeviceGroup
from gpon.api.serializers import OLTStateSerializer
from gpon.models import OLTState
from net_tools.models import DevicesInfo


class TestOLTStateSerializer(TestCase):
    def setUp(self) -> None:
        self.device = Devices.objects.create(
            auth_group=AuthGroup.objects.create(name="test", login="login", password="password"),
            group=DeviceGroup.objects.create(name="test"),
            ip="10.10.10.10",
            name="device1",
        )
        DevicesInfo.objects.create(
            dev=self.device,
            interfaces=json.dumps(
                [
                    {"Interface": "0/1/1"},
                    {"Interface": "0/1/2"},
                    {"Interface": "0/1/3"},
                ]
            ),
        )

    def test_serializer(self):
        serializer = OLTStateSerializer(
            data={
                "deviceName": "device1",
                "devicePort": "0/1/3",
                "fiber": "Волокно",
                "description": "Описание сплиттера 1го каскада\n",
            }
        )
        self.assertTrue(serializer.is_valid())
        self.assertDictEqual(
            serializer.validated_data,
            {
                "device": {"name": "device1"},
                "olt_port": "0/1/3",
                "fiber": "Волокно",
                "description": "Описание сплиттера 1го каскада",
            },
        )
        olt_state = serializer.create(serializer.validated_data)

        self.assertEqual(olt_state.__class__, OLTState)
        self.assertTrue(olt_state.id)
        self.assertEqual(olt_state.device.name, serializer.validated_data["device"]["name"])
        self.assertEqual(olt_state.olt_port, serializer.validated_data["olt_port"])
        self.assertEqual(olt_state.fiber, serializer.validated_data["fiber"])
        self.assertEqual(olt_state.description, serializer.validated_data["description"])

    def test_serializer_half_data(self):
        serializer = OLTStateSerializer(data={"deviceName": "device1", "devicePort": "0/1/3"})
        self.assertTrue(serializer.is_valid())
        self.assertDictEqual(
            serializer.validated_data,
            {
                "device": {"name": "device1"},
                "olt_port": "0/1/3",
            },
        )
        olt_state = serializer.create(serializer.validated_data)

        self.assertEqual(olt_state.__class__, OLTState)
        self.assertTrue(olt_state.id)
        self.assertEqual(olt_state.device.name, serializer.validated_data["device"]["name"])
        self.assertEqual(olt_state.olt_port, serializer.validated_data["olt_port"])
        self.assertEqual(olt_state.fiber, None)
        self.assertEqual(olt_state.description, None)

    def test_serializer_invalid_port(self):
        serializer = OLTStateSerializer(
            data={
                "deviceName": "device1",
                "devicePort": "123",
                "fiber": "Волокно",
                "description": "Описание сплиттера 1го каскада\n",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertDictEqual(
            serializer.errors,
            {
                "devicePort": [
                    ErrorDetail(string="Данное оборудование не имеет порта `123`", code="invalid")
                ]
            },
        )

    def test_serializer_invalid_device_name(self):
        serializer = OLTStateSerializer(
            data={
                "deviceName": "asdfasdf",
                "devicePort": "123",
                "fiber": "Волокно",
                "description": "Описание сплиттера 1го каскада\n",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertDictEqual(
            serializer.errors,
            {
                "deviceName": [
                    ErrorDetail(string="Оборудование `asdfasdf` не существует", code="invalid")
                ]
            },
        )


class TestHouseOLTStateSerializer(TestCase):
    def setUp(self) -> None:
        self.device = Devices.objects.create(
            auth_group=AuthGroup.objects.create(name="test", login="login", password="password"),
            group=DeviceGroup.objects.create(name="test"),
            ip="10.10.10.10",
            name="device1",
        )
        DevicesInfo.objects.create(
            dev=self.device,
            interfaces=json.dumps(
                [
                    {"Interface": "0/1/1"},
                    {"Interface": "0/1/2"},
                    {"Interface": "0/1/3"},
                ]
            ),
        )

    def test_serializer(self):
        pass


data = {
    "oltState": {
        "deviceName": "device1",
        "devicePort": "0/1/3",
        "fiber": "Волокно",
        "description": "Описание сплиттера 1го каскада\n",
    },
    "houseB": {
        "entrances": "1-4",
        "description": "Описание сплиттера 2го каскада",
        "address": {
            "id": 2,
            "region": "Севастополь",
            "settlement": "Севастополь",
            "planStructure": "",
            "street": "улица Колобова",
            "house": "22",
            "block": None,
            "building_type": "building",
            "floors": 9,
            "total_entrances": 22,
        },
    },
    "end3": {
        "type": "splitter",
        "list": [
            {
                "buildAddress": False,
                "address": {
                    "id": 2,
                    "region": "Севастополь",
                    "settlement": "Севастополь",
                    "planStructure": "",
                    "street": "улица Колобова",
                    "house": "22",
                    "block": 10,
                    "building_type": "building",
                    "floors": 1,
                    "total_entrances": 1,
                },
                "location": "3 этаж 1 подъезд",
            },
            {
                "buildAddress": False,
                "address": {
                    "id": 2,
                    "region": "Севастополь",
                    "settlement": "Севастополь",
                    "planStructure": "",
                    "street": "улица Колобова",
                    "house": "22",
                    "block": 10,
                    "building_type": "building",
                    "floors": 1,
                    "total_entrances": 1,
                },
                "location": "3 этаж 2 подъезд",
            },
            {"buildAddress": True, "address": None, "location": "3 этаж 3 подъезд"},
            {"buildAddress": True, "address": None, "location": "3 этаж 4 подъезд"},
        ],
        "existingSplitter": None,
        "portCount": 8,
    },
}
