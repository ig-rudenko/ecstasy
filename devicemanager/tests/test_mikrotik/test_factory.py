from unittest.mock import patch, Mock

from devicemanager.vendors.mikrotik import MikroTik
from ..base_factory_test import AbstractTestFactory


class TestMikroTikFactory(AbstractTestFactory):
    def setUp(self) -> None:
        super().setUp()
        self.mikrotik_version_output = """
                     uptime: 1w1d13h18m46s
                    version: 6.45.9 (long-term)
                 build-time: Apr/30/2020 10:25:34
           factory-software: 6.44.6
                free-memory: 104.5MiB
               total-memory: 128.0MiB
                        cpu: MIPS 74Kc V5.0
                  cpu-count: 1
              cpu-frequency: 800MHz
                   cpu-load: 3%
             free-hdd-space: 3604.0KiB
            total-hdd-space: 16.0MiB
    write-sect-since-reboot: 6720
           write-sect-total: 7591
                 bad-blocks: 0%
          architecture-name: mipsbe
                 board-name: PowerBox Pro
                   platform: MikroTik"""

    @staticmethod
    def get_device_class():
        return MikroTik

    @staticmethod
    def get_output_from_show_version_command() -> str:
        return "bad command name show (line 1 column 1)"

    @patch("devicemanager.vendors.mikrotik.MikrotikFactory.send_command")
    def test_factory_return_class(self, send_command: Mock):
        send_command.return_value = self.mikrotik_version_output
        super().test_factory_return_class()

    @patch("devicemanager.vendors.mikrotik.MikrotikFactory.send_command")
    def test_factory_device_attributes(self, send_command: Mock):
        send_command.return_value = self.mikrotik_version_output
        super().test_factory_device_attributes()


