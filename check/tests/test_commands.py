from django.test import TestCase
from rest_framework.exceptions import ValidationError

from check.models import DeviceGroup, Devices
from check.services.device.commands import validate_command
from devicemanager.device import Interfaces
from net_tools.models import DevicesInfo


class BaseCommandsTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.group = DeviceGroup.objects.create(name="ASW")
        cls.device = Devices.objects.create(
            ip="172.30.0.58",
            name="dev1",
            group=cls.group,
        )
        cls.interfaces = Interfaces(
            [
                {"Interface": "Ethernet1/1", "Status": "up", "Description": "test"},
                {"Interface": "Ethernet1/2", "Status": "up", "Description": "test"},
            ]
        )
        cls.device_info = DevicesInfo(dev=cls.device)
        cls.device_info.update_interfaces_state(cls.interfaces)
        cls.device_info.save()


class TestCommandsPortValidator(BaseCommandsTestCase):

    def test_cmd_port_validator(self):
        command = "show port {port} {port}"
        valid_command = "show port Ethernet1/1 Ethernet1/1"
        context = {"port": {"_": "Ethernet1/1"}}

        res = validate_command(self.device, command, context)
        self.assertEqual(valid_command, res)

    def test_cmd_port_validator_with_name(self):
        command = "show port {port#1} {port#2}"
        valid_command = "show port Ethernet1/1 Ethernet1/2"
        context = {"port": {"1": "Ethernet1/1", "2": "Ethernet1/2"}}

        res = validate_command(self.device, command, context)
        self.assertEqual(valid_command, res)

    def test_cmd_port_validator_with_missed_name(self):
        command = "show port {port#1} {port#2}"
        context = {"port": {"1": "Ethernet1/1"}}

        with self.assertRaises(ValidationError):
            validate_command(self.device, command, context)

    def test_cmd_port_validator_with_3_name(self):
        command = "show port {port#1} {port#2} {port#1}"
        valid_command = "show port Ethernet1/1 Ethernet1/2 Ethernet1/1"
        context = {"port": {"1": "Ethernet1/1", "2": "Ethernet1/2"}}

        res = validate_command(self.device, command, context)
        self.assertEqual(valid_command, res)


class TestCommandsIPValidator(BaseCommandsTestCase):

    def test_cmd_ip_validator(self):
        command = "show ip {ip} {ip}"
        valid_command = "show ip 172.30.0.58 172.30.0.58"
        context = {"ip": {"_": "172.30.0.58"}}

        res = validate_command(self.device, command, context)
        self.assertEqual(valid_command, res)

    def test_cmd_ip_validator_with_name(self):
        command = "show ip {ip#1} {ip#2}"
        valid_command = "show ip 172.30.0.58 10.10.10.10"
        context = {"ip": {"1": "172.30.0.58", "2": "10.10.10.10"}}

        res = validate_command(self.device, command, context)
        self.assertEqual(valid_command, res)

    def test_cmd_ip_validator_with_missed_name(self):
        command = "show ip {ip#1} {ip#2}"
        context = {"ip": {"1": "172.30.0.58"}}

        with self.assertRaises(ValidationError):
            validate_command(self.device, command, context)

    def test_cmd_ip_validator_with_3_name(self):
        command = "show ip {ip#1} {ip#2} {ip#1}"
        valid_command = "show ip 172.30.0.58 10.10.10.10 172.30.0.58"
        context = {"ip": {"1": "172.30.0.58", "2": "10.10.10.10"}}

        res = validate_command(self.device, command, context)
        self.assertEqual(valid_command, res)


class TestCommandsMACValidator(BaseCommandsTestCase):
    def test_cmd_mac_validator(self):
        command = "show mac {mac} {mac}"
        valid_command = "show mac 00:00:00:00:00:00 00:00:00:00:00:00"
        context = {"mac": {"_": "00:00:00:00:00:00"}}

        res = validate_command(self.device, command, context)
        self.assertEqual(valid_command, res)

    def test_cmd_mac_validator_with_name(self):
        command = "show mac {mac#1} {mac#2}"
        valid_command = "show mac 00:00:00:00:00:00 aa:00:00:00:00:aa"
        context = {"mac": {"1": "00:00:00:00:00:00", "2": "aa:00:00:00:00:aa"}}

        res = validate_command(self.device, command, context)
        self.assertEqual(valid_command, res)

    def test_cmd_mac_validator_with_missed_name(self):
        command = "show mac {mac#1} {mac#2}"
        context = {"mac": {"1": "00:00:00:00:00:00"}}

        with self.assertRaises(ValidationError):
            validate_command(self.device, command, context)

    def test_cmd_mac_validator_with_invalid_mac(self):
        command = "show mac {mac#1}"
        context = {"mac": {"1": "invalid_mac"}}

        with self.assertRaises(ValidationError):
            validate_command(self.device, command, context)

    def test_cmd_mac_validator_with_3_name(self):
        command = "show mac {mac#1} {mac#2} {mac#1}"
        valid_command = "show mac 00:00:00:00:00:00 aa:00:00:00:00:aa 00:00:00:00:00:00"
        context = {"mac": {"1": "00:00:00:00:00:00", "2": "aa:00:00:00:00:aa"}}

        res = validate_command(self.device, command, context)
        self.assertEqual(valid_command, res)


class TestCommandsNumberValidator(BaseCommandsTestCase):
    def test_cmd_number_validator(self):
        command = "show port {number} {number}"
        valid_command = "show port 1 1"
        context = {"number": {"_": "1"}}

        res = validate_command(self.device, command, context)
        self.assertEqual(valid_command, res)

    def test_cmd_number_validator_with_name(self):
        command = "show port {number#first} {number#second}"
        valid_command = "show port 1 2"
        context = {"number": {"first": "1", "second": "2"}}

        res = validate_command(self.device, command, context)
        self.assertEqual(valid_command, res)

    def test_cmd_number_validator_with_missed_name(self):
        command = "show port {number#first} {number#second}"
        context = {"number": {"first": "1"}}

        with self.assertRaises(ValidationError):
            validate_command(self.device, command, context)

    def test_cmd_number_validator_with_3_name(self):
        command = "show port {number#1} {number#2} {number#1}"
        valid_command = "show port 1 2 1"
        context = {"number": {"1": "1", "2": "2"}}

        res = validate_command(self.device, command, context)
        self.assertEqual(valid_command, res)

    def test_cmd_number_validator_with_invalid_number(self):
        command = "show port {number#1}"
        context = {"number": {"1": "invalid_number"}}

        with self.assertRaises(ValidationError):
            validate_command(self.device, command, context)

    def test_cmd_number_validator_with_float_number(self):
        command = "show port {number#1}"
        context = {"number": {"1": "1.0"}}

        with self.assertRaises(ValidationError):
            validate_command(self.device, command, context)

    def test_cmd_number_validator_with_negative_number(self):
        command = "show port {number#1}"
        valid_command = "show port -1"
        context = {"number": {"1": "-1"}}

        res = validate_command(self.device, command, context)
        self.assertEqual(valid_command, res)

    def test_cmd_number_validator_with_zero(self):
        command = "show port {number#1}"
        valid_command = "show port 0"
        context = {"number": {"1": "0"}}

        res = validate_command(self.device, command, context)
        self.assertEqual(valid_command, res)

    def test_cmd_number_validator_with_start_pos(self):
        command = "show port {number:1}"
        valid_command = "show port 2"
        context = {"number": {"_": "2"}}

        res = validate_command(self.device, command, context)
        self.assertEqual(valid_command, res)

    def test_cmd_number_validator_with_end_pos(self):
        command = "show port {number::10}"
        valid_command = "show port 3"
        context = {"number": {"_": "3"}}

        res = validate_command(self.device, command, context)
        self.assertEqual(valid_command, res)

    def test_cmd_number_validator_with_pos_range(self):
        command = "show port {number:1:10}"
        valid_command = "show port 5"
        context = {"number": {"_": "5"}}

        res = validate_command(self.device, command, context)
        self.assertEqual(valid_command, res)

    def test_cmd_number_validator_with_start_neg(self):
        command = "show port {number:-1}"
        valid_command = "show port -1"
        context = {"number": {"_": "-1"}}

        res = validate_command(self.device, command, context)
        self.assertEqual(valid_command, res)

    def test_cmd_number_validator_with_end_neg(self):
        command = "show port {number::-1}"
        valid_command = "show port -2"
        context = {"number": {"_": "-2"}}

        res = validate_command(self.device, command, context)
        self.assertEqual(valid_command, res)

    def test_cmd_number_validator_with_neg_range(self):
        command = "show port {number:-10:-1}"
        valid_command = "show port -5"
        context = {"number": {"_": "-5"}}

        res = validate_command(self.device, command, context)
        self.assertEqual(valid_command, res)

    def test_cmd_number_validator_with_invalid_start_pos(self):
        command = "show port {number:10}"
        context = {"number": {"_": "1"}}

        with self.assertRaises(ValidationError):
            validate_command(self.device, command, context)

    def test_cmd_number_validator_with_invalid_end_pos(self):
        command = "show port {number::10}"
        context = {"number": {"_": "55"}}

        with self.assertRaises(ValidationError):
            validate_command(self.device, command, context)

    def test_cmd_number_validator_with_invalid_pos_range(self):
        command = "show port {number:10:1}"
        context = {"number": {"_": "1"}}

        with self.assertRaises(ValidationError):
            validate_command(self.device, command, context)

    def test_cmd_number_validator_with_invalid_neg_range(self):
        command = "show port {number:-1:-10}"
        context = {"number": {"_": "-1"}}

        with self.assertRaises(ValidationError):
            validate_command(self.device, command, context)

    def test_cmd_number_validator_with_names(self):
        command = "show port {number:-1:10#range} {number:1:4096#vlan}"
        valid_command = "show port 5 1234"
        context = {"number": {"range": "5", "vlan": "1234"}}

        res = validate_command(self.device, command, context)
        self.assertEqual(valid_command, res)


class TestMixedValidator(BaseCommandsTestCase):
    def test_mixed_validator(self):
        command = "show port {port} {ip#1} {mac#2} {port#1}"
        valid_command = "show port Ethernet1/1 172.30.0.58 aa:00:00:00:00:aa Ethernet1/2"
        context = {
            "port": {"_": "Ethernet1/1", "1": "Ethernet1/2"},
            "ip": {"1": "172.30.0.58"},
            "mac": {"2": "aa:00:00:00:00:aa"},
        }

        res = validate_command(self.device, command, context)
        self.assertEqual(valid_command, res)
