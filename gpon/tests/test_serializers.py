import copy
import json

from django.test import TestCase
from rest_framework.exceptions import ErrorDetail, ValidationError

from check.models import Devices, AuthGroup, DeviceGroup
from gpon.api.serializers.address import AddressSerializer, BuildingAddressSerializer
from gpon.api.serializers.common import End3Serializer
from gpon.api.serializers.create_tech_data import (
    OLTStateSerializer,
    HouseOLTStateSerializer,
    CreateTechDataSerializer,
)
from gpon.models import OLTState, Address, HouseB, HouseOLTState, TechCapability, End3
from gpon.tests.data import CREATE_TECH_DATA
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


class TestAddressSerializer(TestCase):
    def test_street_validator(self):
        self.assertEqual(
            AddressSerializer.validate_street("   улицаКолобова"),
            "УЛИЦА КОЛОБОВА",
        )
        self.assertEqual(
            AddressSerializer.validate_street("улица Колобова"),
            "УЛИЦА КОЛОБОВА",
        )
        self.assertEqual(
            AddressSerializer.validate_street("Улица Колобова   "),
            "УЛИЦА КОЛОБОВА",
        )
        self.assertEqual(
            AddressSerializer.validate_street("ул.Колобова"),
            "УЛИЦА КОЛОБОВА",
        )
        self.assertEqual(
            AddressSerializer.validate_street("Ул.Колобова"),
            "УЛИЦА КОЛОБОВА",
        )
        self.assertEqual(
            AddressSerializer.validate_street("ул.   Колобова"),
            "УЛИЦА КОЛОБОВА",
        )
        self.assertEqual(
            AddressSerializer.validate_street("   УЛ. КолоБова   "),
            "УЛИЦА КОЛОБОВА",
        )
        self.assertEqual(
            AddressSerializer.validate_street("ул. Колобова"),
            "УЛИЦА КОЛОБОВА",
        )
        self.assertEqual(
            AddressSerializer.validate_street("ул Колобова"),
            "УЛИЦА КОЛОБОВА",
        )
        self.assertEqual(
            AddressSerializer.validate_street("ул Колобова"),
            "УЛИЦА КОЛОБОВА",
        )

        # Без указания типа
        with self.assertRaises(ValidationError):
            AddressSerializer.validate_street("Колобова")

    def test_prospect_validator(self):
        self.assertEqual(
            AddressSerializer.validate_street("   пр-кт.Генерала Острякова"),
            "ПРОСПЕКТ ГЕНЕРАЛА ОСТРЯКОВА",
        )
        self.assertEqual(
            AddressSerializer.validate_street("пр-кт Генерала Острякова"),
            "ПРОСПЕКТ ГЕНЕРАЛА ОСТРЯКОВА",
        )
        self.assertEqual(
            AddressSerializer.validate_street("просп Генерала Острякова   "),
            "ПРОСПЕКТ ГЕНЕРАЛА ОСТРЯКОВА",
        )
        self.assertEqual(
            AddressSerializer.validate_street("просп.Генерала Острякова"),
            "ПРОСПЕКТ ГЕНЕРАЛА ОСТРЯКОВА",
        )
        self.assertEqual(
            AddressSerializer.validate_street("пр-кт.   генерала острякова"),
            "ПРОСПЕКТ ГЕНЕРАЛА ОСТРЯКОВА",
        )
        self.assertEqual(
            AddressSerializer.validate_street("просп.   Генерала Острякова"),
            "ПРОСПЕКТ ГЕНЕРАЛА ОСТРЯКОВА",
        )

        # Без указания типа
        with self.assertRaises(ValidationError):
            AddressSerializer.validate_street("генерала Острякова")

    def test_serializer_validator(self):
        ser = AddressSerializer(
            data={
                "region": "Севастополь",
                "settlement": "Севастополь",
                "planStructure": "Маяк",
                "street": "ул. Весенняя",
                "house": "22в",
            }
        )
        self.assertTrue(ser.is_valid())
        self.assertDictEqual(
            ser.validated_data,
            {
                "region": "СЕВАСТОПОЛЬ",
                "settlement": "СЕВАСТОПОЛЬ",
                "plan_structure": "МАЯК",
                "street": "УЛИЦА ВЕСЕННЯЯ",
                "house": "22В",
            },
        )

        address1 = ser.create(ser.validated_data)
        address2 = ser.create(ser.validated_data)
        # Повторно такой же адрес не будет создаваться, а вернется имеющийся
        self.assertEqual(Address.objects.count(), 1)
        self.assertEqual(address1, address2)


class TestHouseOLTStateSerializer(TestCase):
    def test_serializer(self):
        data = {
            "entrances": "1-4",
            "description": "Описание сплиттера 2го каскада",
            "address": {
                "id": 2,
                "region": "Севастополь",
                "settlement": "Севастополь",
                "street": "улица Колобова",
                "house": "22",
                "block": None,
                "building_type": "building",
                "floors": 9,
                "total_entrances": 22,
            },
        }

        serializer = HouseOLTStateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), msg="Данные сериализатора неверные")
        house_olt_state = serializer.create(serializer.validated_data)

        self.assertEqual(Address.objects.count(), 1)  # Имеется новый адрес
        self.assertEqual(HouseB.objects.count(), 1)  # Добавлен дом
        self.assertEqual(HouseOLTState.objects.count(), 1)  # Имеется OLT State

        # Созданный адрес имеется у дома
        self.assertEqual(Address.objects.first().id, house_olt_state.house.address.id)
        self.assertEqual(HouseB.objects.first().id, house_olt_state.house.id)

        # Повторное создание не добавит новые записи в базу
        serializer = HouseOLTStateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        serializer.create(serializer.validated_data)
        self.assertEqual(HouseB.objects.count(), 1)  # Дом все еще один
        self.assertEqual(Address.objects.count(), 1)  # Адрес все еще один
        self.assertEqual(HouseOLTState.objects.count(), 2)  # OLT State Изменился


class TestCreateTechDataSerializer(TestCase):
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
        self.data = copy.deepcopy(CREATE_TECH_DATA)

    def test_serializer_no_end3(self):
        data = copy.deepcopy(self.data)
        del data["end3"]

        serializer = CreateTechDataSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertDictEqual(
            serializer.errors,
            {
                "end3": [
                    ErrorDetail(
                        string="Обязательный параметр для данных splitter/rizer", code="required"
                    )
                ]
            },
        )

    def test_serializer_no_oltState(self):
        data = copy.deepcopy(self.data)
        del data["oltState"]

        serializer = CreateTechDataSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertDictEqual(
            serializer.errors,
            {
                "oltState": [
                    ErrorDetail(
                        string="Обязательный параметр для данных OLT состояния", code="required"
                    )
                ]
            },
        )

    def test_serializer_no_houseB(self):
        data = copy.deepcopy(self.data)
        del data["houseB"]

        serializer = CreateTechDataSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertDictEqual(
            serializer.errors,
            {
                "houseB": [
                    ErrorDetail(string="Обязательный параметр для данных строения", code="required")
                ]
            },
        )

    def test_serializer_invalid_street_address(self):
        data = copy.deepcopy(self.data)
        data["houseB"]["address"]["street"] = "123"

        serializer = CreateTechDataSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertDictEqual(
            serializer.errors,
            {
                "houseB": {
                    "address": {
                        "street": [
                            ErrorDetail(
                                string="Укажите полное название с указанием типа "
                                "(улица/проспект/площадь/проезд/бульвар/шоссе/переулок/тупик)",
                                code="invalid",
                            )
                        ]
                    }
                }
            },
        )

    def test_serializer_invalid_address(self):
        data = copy.deepcopy(self.data)
        del data["houseB"]["address"]["street"]

        serializer = CreateTechDataSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        print(serializer.errors)
        self.assertDictEqual(
            serializer.errors,
            {
                "houseB": {
                    "address": {
                        "non_field_errors": [
                            ErrorDetail(
                                string="Необходимо указать либо СНТ ТСН, либо улицу", code="invalid"
                            )
                        ]
                    }
                }
            },
        )

    def test_serializer_empty_end3_list(self):
        data = copy.deepcopy(self.data)
        data["end3"]["list"] = []

        serializer = CreateTechDataSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertDictEqual(
            serializer.errors,
            {
                "end3": {
                    "non_field_errors": [
                        ErrorDetail(
                            string="Необходимо выбрать хотя бы один splitter/rizer", code="invalid"
                        )
                    ]
                }
            },
        )

    def test_serializer_invalid_end3_type(self):
        data = copy.deepcopy(self.data)
        data["end3"]["type"] = "asdasd"

        serializer = CreateTechDataSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertDictEqual(
            serializer.errors,
            {
                "end3": {
                    "type": [
                        ErrorDetail(
                            string="Абонентская линия должна быть либо splitter, либо rizer.",
                            code="invalid_choice",
                        )
                    ]
                }
            },
        )

    def test_serializer_invalid_end3(self):
        """
        Проверяем, что для каждого splitter/rizer должно быть указано поле `location`
        """
        data = copy.deepcopy(self.data)
        del data["end3"]["list"][2]["location"]

        serializer = CreateTechDataSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertDictEqual(
            serializer.errors,
            {
                "end3": {
                    "list": [
                        {},
                        {},
                        {"location": [ErrorDetail(string="Обязательное поле.", code="required")]},
                        {},
                    ]
                }
            },
        )

    def test_serializer(self):
        serializer = CreateTechDataSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertDictEqual(
            serializer.validated_data,
            {
                "oltState": {
                    "device": {"name": "device1"},
                    "olt_port": "0/1/3",
                    "fiber": "Волокно",
                    "description": "Описание сплиттера 1го каскада",
                },
                "houseB": {
                    "house": {
                        "address": {
                            "region": "СЕВАСТОПОЛЬ",
                            "settlement": "СЕВАСТОПОЛЬ",
                            "street": "УЛИЦА КОЛОБОВА",
                            "house": "22",
                            "block": None,
                            "building_type": "building",
                            "floors": 9,
                            "total_entrances": 22,
                        }
                    },
                    "entrances": "1-4",
                    "description": "Описание сплиттера 2го каскада",
                },
                "end3": {
                    "type": "splitter",
                    "existingSplitter": None,
                    "portCount": 8,
                    "list": [
                        {
                            "address": {
                                "region": "СЕВАСТОПОЛЬ",
                                "settlement": "СЕВАСТОПОЛЬ",
                                "street": "УЛИЦА КОЛОБОВА",
                                "house": "22",
                                "block": 10,
                            },
                            "buildAddress": False,
                            "location": "3 этаж 1 подъезд",
                        },
                        {
                            "address": {
                                "region": "СЕВАСТОПОЛЬ",
                                "settlement": "СЕВАСТОПОЛЬ",
                                "street": "УЛИЦА КОЛОБОВА",
                                "house": "22",
                                "block": 10,
                            },
                            "buildAddress": False,
                            "location": "3 этаж 2 подъезд",
                        },
                        {"address": None, "buildAddress": True, "location": "3 этаж 3 подъезд"},
                        {"address": None, "buildAddress": True, "location": "3 этаж 4 подъезд"},
                    ],
                },
            },
        )
        olt_state = serializer.create(serializer.validated_data)

        # Проверяем правильность заполнения oltState
        self.assertEqual(olt_state.olt_port, self.data["oltState"]["devicePort"])
        self.assertEqual(olt_state.device.name, self.data["oltState"]["deviceName"])
        self.assertEqual(olt_state.fiber, self.data["oltState"]["fiber"].strip())
        self.assertEqual(olt_state.description, self.data["oltState"]["description"].strip())

        # Проверяем правильность заполнения houseB
        house: HouseB = olt_state.houses.first()
        self.assertEqual(house.total_entrances, self.data["houseB"]["address"]["total_entrances"])
        self.assertEqual(house.floors, self.data["houseB"]["address"]["floors"])
        self.assertEqual(
            house.apartment_building, self.data["houseB"]["address"]["building_type"] == "building"
        )

        # Всего две записи адреса (1я для дома, 2я для сплиттеров)
        self.assertEqual(Address.objects.count(), 2)

        # Проверяем сплиттера
        total_end3_records_count = 4
        self.assertEqual(house.house_olt_states.first().end3_set.count(), total_end3_records_count)
        # Технической возможности должно быть столько, как указанных портов на каждом сплиттере
        self.assertEqual(
            TechCapability.objects.count(),
            total_end3_records_count * self.data["end3"]["portCount"],  # 4 * 8
        )

    def test_serializer_with_existing_splitter_field(self):
        data = copy.deepcopy(self.data)
        del data["end3"]["list"]
        data["end3"]["existingSplitter"] = {"id": 55555}

        serializer = CreateTechDataSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertDictEqual(
            serializer.errors,
            {
                "end3": {
                    "existingSplitter": [
                        ErrorDetail(string="Сплиттер с id=55555 не существует", code="invalid")
                    ]
                }
            },
        )


class TestBuildingAddressSerializer(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        HouseB.objects.create(
            address=Address.objects.create(street="улица Колобова", house="22", block=10),
            apartment_building=True,
            floors=9,
            total_entrances=10,
        )
        HouseB.objects.create(
            address=Address.objects.create(street="улица Колобова", house="12", block=None),
            apartment_building=True,
            floors=9,
            total_entrances=11,
        )
        HouseB.objects.create(
            address=Address.objects.create(plan_structure="Вишня", house="11", block=1),
            apartment_building=False,
            floors=9,
            total_entrances=12,
        )
        HouseB.objects.create(
            address=Address.objects.create(
                plan_structure="Вишня", street="улица Вишневая", house="9", block=None
            ),
            apartment_building=False,
            floors=9,
            total_entrances=13,
        )

    def test_serializer(self):
        serializer = BuildingAddressSerializer(instance=HouseB.objects.all(), many=True)
        data = serializer.data
        print(data)
        self.assertEqual(len(data), 4)
        self.assertEqual(data[0].keys(), data[3].keys())
        self.assertTupleEqual(
            tuple(data[0].keys()),
            (
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
            ),
        )


class TestEnd3Serializer(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        address = Address.objects.create(street="улица Колобова", house="22", block=10)
        End3.objects.create(address=address, capacity=8, type="splitter", location="подъезд 1")
        End3.objects.create(address=address, capacity=8, type="splitter", location="подъезд 2")
        End3.objects.create(address=address, capacity=8, type="splitter", location="подъезд 3")
        End3.objects.create(address=address, capacity=8, type="splitter", location="подъезд 4")

    def test_serializer(self):
        serializer = End3Serializer(instance=End3.objects.all(), many=True)
        data = serializer.data
        self.assertEqual(len(data), 4)
        self.assertEqual(data[0].keys(), data[3].keys())
        self.assertTupleEqual(
            tuple(data[0].keys()),
            ("id", "address", "capacity", "location", "type"),
        )
        self.assertTupleEqual(
            tuple(data[0]["address"].keys()),
            (
                "region",
                "settlement",
                "planStructure",
                "street",
                "house",
                "block",
                "floor",
                "apartment",
            ),
        )
