from django.test import TestCase

from gpon.api.serializers.create_subscriber_data import CreateSubscriberDataSerializer
from gpon.models import Service, End3


class TestCreateSerializer(TestCase):
    def setUp(self) -> None:
        self.services = ["internet", "static"]
        for service in self.services:
            Service.objects.create(name=service)

        self.end3 = End3.objects.create(
            location="location",
            type=End3.Type.splitter.value,
            capacity=2,
        )
        self.tech_capability = self.end3.techcapability_set.first()

        self.data = {
            "customer": {
                "id": 2,
                "type": "person",
                "firstName": "Иван",
                "surname": "Иванов",
                "lastName": "Иванович",
                "companyName": "",
                "contract": 12312,
                "phone": "+7 (312) 368-45-62",
            },
            "tech_capability": self.tech_capability.id,
            "transit": 312312,
            "order": 34563456,
            "services": self.services,
            "ip": None,
            "ont_id": 1,
            "ont_serial": "47567345634",
            "ont_mac": "aa-AA.bb-BB.99-00",
            "connected_at": "2023-10-12T13:16:08.000Z",
            "address": {
                "id": 1,
                "region": "Севастополь",
                "settlement": "Севастополь",
                "planStructure": "",
                "street": "улица Колобова",
                "house": "226",
                "block": None,
                "building_type": "building",
                "floors": 9,
                "total_entrances": 11,
                "floor": 5,
                "apartment": 23,
            },
        }

    def test_create_serializer(self):
        serializer = CreateSubscriberDataSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        print(serializer.errors)
        print(serializer.validated_data)
        serializer.save()
