from django.test import SimpleTestCase

from devicemanager.vendors.juniper import Juniper


class FakeJuniperSession:
    def __init__(self):
        self._output = b""

    @staticmethod
    def expect(*args, **kwargs):
        return 0

    @property
    def before(self):
        return self._output

    def send(self, command, *args, **kwargs):
        return self.sendline(command, *args, **kwargs)

    def sendline(self, command, *args, **kwargs):
        if "show interfaces description" in command:
            self._output = b"""
Interface       Admin Link Description
ae1.123         up    up   ### VLAN 123
ae1.1234        up    up   ### VLAN 1234
ae2             down  down   
ae2.2           up    down
fxp0            up    up   Management
lo0.2           up    up   Loopback Interface user white networks
"""


class TestJuniperAddressParser(SimpleTestCase):
    def test_interfaces_parser(self):
        juniper = Juniper(session=FakeJuniperSession(), ip="10.10.10.10", auth={})
        interfaces = [
            ("ae1.123", "up", "### VLAN 123"),
            ("ae1.1234", "up", "### VLAN 1234"),
            ("ae2", "admin down", ""),
            ("ae2.2", "down", ""),
            ("fxp0", "up", "Management"),
            ("lo0.2", "up", "Loopback Interface user white networks"),
        ]
        juniper.get_interfaces()
        self.assertListEqual(juniper.get_interfaces(), interfaces)

    def test_subscribers_parser(self):
        juniper = Juniper(session=FakeJuniperSession(), ip="10.10.10.10", auth={})
        subscribers_output1 = """...
            IP Address: 10.201.170.140
            ...
            MAC Address: c0:25:e9:46:77:0f
            ...
            VLAN Id: 604
            Agent Circuit ID: port1
            Agent Remote ID: Device_name
            Login Time ...
        """
        subscribers_output2 = """...
            IP Address: 10.201.170.140
            ...
            MAC Address: c0:25:e9:46:77:0f
            ...
            VLAN Id: 604
            Agent Circuit ID: 70 6f 72 74 31
            Agent Remote ID: 44 65 76 69 
            63 65 5f 6e 61 6d 65
            Login Time ...
        """
        valid_data = [
            "10.201.170.140",
            "c0:25:e9:46:77:0f",
            "604",
            "Device_name",
            "port1",
        ]

        self.assertEqual(juniper._parse_subscribers(subscribers_output1), valid_data)

        self.assertEqual(juniper._parse_subscribers(subscribers_output2), valid_data)
