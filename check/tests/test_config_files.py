from django.test import TestCase

from check.api.serializers import ConfigFileSerializer
from gathering.services.configurations.local_storage import ConfigFile


class TestConfigFile(TestCase):
    def test_serializer(self):
        files = [
            ConfigFile(
                name=f"name-{i}",
                size=4096 * i,
                modTime="12:14 / 01.02.2023",
            )
            for i in range(5)
        ]

        ConfigFileSerializer(files, many=True)
