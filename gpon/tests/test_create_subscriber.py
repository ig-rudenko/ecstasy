from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from gpon.api.serializers.create_subscriber_data import SubscriberDataSerializer
from gpon.models import Address, Customer, End3, Service, SubscriberConnection, TechCapability


class TestSubscriberDataCreation(APITestCase):
    def setUp(self) -> None:
        self.superuser = get_user_model().objects.create_superuser(
            username="TestSubscriberDataCreation-superuser", password="password"
        )
        self.services = ["internet", "static"]
        for service in self.services:
            Service.objects.create(name=service)

        self.end3: End3 = End3.objects.create(
            location="location",
            type=End3.Type.splitter.value,
            capacity=2,
        )
        self.tech_capability: TechCapability = self.end3.techcapability_set.first()  # type: ignore
        self.valid_mac = "aaaabbbb9900"

        self.data = {
            "customer": {
                "id": 2,
                "type": "person",
                "firstName": "Иван",
                "surname": "Иванов",
                "lastName": "Иванович",
                "companyName": None,
                "contract": 12312,
                "phone": "+7 (312) 368-45-62",
            },
            "tech_capability": self.tech_capability.id,
            "transit": 312312,
            "order": 34563456,
            "services": self.services,
            "ip": "192.168.0.1",
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
        serializer = SubscriberDataSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        # serializer.is_valid()
        print(serializer.errors)
        print(serializer.validated_data)
        serializer.save()
        self._after_created()

    def test_create_api_view(self):
        self.client.force_login(self.superuser)
        resp = self.client.post(
            reverse("gpon-api:subscribers-data-list-create"), data=self.data, format="json"
        )
        self.assertEqual(resp.status_code, 201)
        self._after_created()

    def _after_created(self):
        print("_after_created")
        self.assertEqual(Customer.objects.count(), 1)
        self.tech_capability.refresh_from_db()
        self.assertEqual(self.tech_capability.status, TechCapability.Status.active.value)

        customer = Customer.objects.get(
            type=self.data["customer"]["type"],
            first_name=self.data["customer"]["firstName"],
            surname=self.data["customer"]["surname"],
            last_name=self.data["customer"]["lastName"],
            company_name=self.data["customer"]["companyName"],
            contract=str(self.data["customer"]["contract"]),
            phone=self.data["customer"]["phone"],
        )

        self.assertEqual(SubscriberConnection.objects.count(), 1)
        self.assertEqual(Address.objects.count(), 1)
        connection = SubscriberConnection.objects.get(customer=customer)
        self.assertEqual(connection.tech_capability.id, self.tech_capability.id)
        self.assertEqual(connection.transit, self.data["transit"])
        self.assertEqual(connection.order, str(self.data["order"]))
        self.assertEqual(connection.ip, self.data["ip"])
        self.assertEqual(connection.ont_id, self.data["ont_id"])
        self.assertEqual(connection.ont_serial, self.data["ont_serial"])
        self.assertEqual(connection.ont_mac, self.valid_mac)
