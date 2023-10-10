from django.test import TestCase

from gpon.api.serializers.view_tech_data import End3TechCapabilitySerializer
from gpon.models import End3, TechCapability, Address


class TestEnd3TechCapabilitySerializer(TestCase):
    def setUp(self) -> None:
        End3.objects.create(location="Местоположение", type="splitter", capacity=8)

    def test_autocreate_tech_capability(self):
        self.assertEqual(
            TechCapability.objects.count(),
            8,
            msg="Техническая возможность не создалась автоматически",
        )

    def test_end3_update_tech_capacity(self):
        """
        Функция проверяет обновление технических возможностей для экземпляра модели End3,
        гарантируя правильное обновление количества технических возможностей и сохранение порядка нумерации.
        """
        end3 = End3.objects.first()
        self.assertEqual(end3.techcapability_set.count(), 8)

        for update_capacity_count in [4, 8, 16]:
            serializer = End3TechCapabilitySerializer(
                instance=end3,
                data={"capacity": update_capacity_count},
                partial=True,
            )
            self.assertTrue(serializer.is_valid())
            serializer.save()

            self.assertEqual(end3.techcapability_set.count(), update_capacity_count)
            # Проверяем порядок нумерации
            for i, tech in enumerate(end3.techcapability_set.all().order_by("number"), 1):
                self.assertEqual(
                    tech.number, i, msg="Порядок нумерации после изменения ёмкости был нарушен"
                )

    def test_end3_update_location(self):
        end3 = End3.objects.first()
        new_location = "new_location"

        serializer = End3TechCapabilitySerializer(
            instance=end3,
            data={"location": new_location},
            partial=True,
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()

        self.assertEqual(end3.location, new_location)

    def test_end3_update_address(self):
        end3 = End3.objects.first()
        self.assertIsNone(end3.address)  # Изначально адреса нет

        address = {
            "region": "Севастополь",
            "settlement": "Севастополь",
            "planStructure": "",
            "street": "улица Колобова",
            "house": "22А",
            "block": None,
            "floor": None,
            "apartment": None,
        }

        serializer = End3TechCapabilitySerializer(
            instance=end3,
            data={"address": address},
            partial=True,
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()

        self.assertEqual(Address.objects.first(), end3.address)
