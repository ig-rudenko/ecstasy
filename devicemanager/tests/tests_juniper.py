from django.test import SimpleTestCase
from devicemanager.vendors.juniper import Juniper


class TestJuniperAddressParser(SimpleTestCase):
    def test_subscribers_parser(self):
        juniper = Juniper(session=None, ip="10.10.10.10", auth={})
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
