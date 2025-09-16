import re

from django.test import SimpleTestCase

from devicemanager.vendors.iskratel import IskratelMBan

from .base_factory_test import AbstractTestFactory


class TestIskratelMBanFactory(AbstractTestFactory):
    @staticmethod
    def get_device_class():
        return IskratelMBan

    @staticmethod
    def get_output_from_show_version_command() -> str:
        return """Package dir: /tffs/MYGS0A53

------------------ binary file's versions ------------------

   SGM01/CDI01:  E:/PACKAGES/ba6054ax/MYGS0A53  Apr 25 2014 10:38:29

------------------ MAIN run-time ----------------------------

Steer version: MYGS0A53

   SGM01/CDI01: as in binary file

------------------ HW  &  SW  INFORMATION -------------------

               V x W o r k s

     IL steer: MVVS0A08
  BSP version: 1.0/5
          CPU: IskraTEL CDI PMC board
      VxWorks: 5.4.2
       Kernel: WIND version 2.5
 ADSL2PLUS over POTS GS firmware version:  E.67.1.102


------------------------------------------------------------"""


class FakeIskratelMBanSession:
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
        if command == "show dsl port\n":
            self._output = b"""mBAN> show dsl port

ADSL ports:
Port   Name                   Profile Name             Equipment  Operational St.
-------------------------------------------------------------------------------------
 1   test                     N160-1856/608-6432Anne#  Equipped   Down/In service
 2   312312312312-536042      N320-2464/2464-12896An#  Equipped   Down/In service
 3                            N608-3008/4896-18720An#  Equipped   Up/In service
 4   636033_ADSL_Port4        N320-2464/2464-12896An#  Equipped   Down/In service
 5                            N608-3008/4896-18720An#  Unequipped
 6   312311424435-1297399     N160-1856/608-6432Anne#  Equipped   Up/In service
 """
        elif "show bridge mactable interface dsl" in command:
            self._output = b"""
Current MAC addresses        : 11:22:6E:89:8B:98
"""
        elif "show bridge mactable interface fasteth" in command:
            self._output = b"""
Current MAC addresses        : 11:22:48:8F:78:F2
                               11:22:82:46:54:71
                               11:22:82:45:14:7F
"""
        elif "show dsl profile" in command:
            self._output = b"""
145   N160-1856/608-6432AnnexM
139   N160-928/608-4896Adsl2+
100   N160/320ADSL2+"""

        elif re.match(r"show dsl port \d+ detail", command):
            self._output = b"""
Port                           6
Name                           380692636162-1297399
Type                           ADSL2+ over POTS
Profile Name                   N160-1856/608-6432AnnexM
Bin Profile Name               All BINs enabled
Equipment                      Equipped
Operational State              Up/In service
DSL State                      Active
Service Type                   ADSL2PLUS
DS Data Rate AS0               6400 kbit/s    US Data Rate LS0                928 kbit/s
DS Attenuation                   34 dB        US Attenuation                   21 dB
DS SNR Margin                    13 dB        US SNR Margin                    12 dB
Total DS output power            20 dB
DS interleaved delay              7 ms        US interleaved delay              7 ms
PM State                       L0 - Full on

Current Trellis operation mode                                              Active

Number of DS parity bytes per RS Codeword assigned to interleaved buffer      16
Number of DS symbols per RS Codeword assigned to interleaved buffer          0.5
DS interleaved RS Codeword depth value                                       32
Maximum DS attainable aggregate rate                                       8128 kbit/s

Number of US parity bytes per RS Codeword assigned to interleaved buffer      16
Number of US symbols per RS Codeword assigned to interleaved buffer          0.5
US interleaved RS Codeword depth value                                        4
Maximum US attainable aggregate rate                                       1120 kbit/s
"""


class TestIskratelMBan(SimpleTestCase):
    def setUp(self) -> None:
        self.device = IskratelMBan(
            session=FakeIskratelMBanSession(),
            ip="10.10.10.10",
            snmp_community="",
            auth={
                "login": "user",
                "password": "passwd",
                "privilege_mode_password": "secret",
            },
        )

    def test_get_interfaces(self):
        res = self.device.get_interfaces()
        self.assertEqual(
            res,
            [
                ("1", "down", "test"),
                ("2", "down", "312312312312-536042"),
                ("3", "up", ""),
                ("4", "down", "636033_ADSL_Port4"),
                ("5", "admin down", ""),
                ("6", "up", "312311424435-1297399"),
            ],
        )

    def test_get_vlans(self):
        res = self.device.get_vlans()
        self.assertEqual(
            res,
            [
                ("1", "down", "test", []),
                ("2", "down", "312312312312-536042", []),
                ("3", "up", "", []),
                ("4", "down", "636033_ADSL_Port4", []),
                ("5", "admin down", "", []),
                ("6", "up", "312311424435-1297399", []),
            ],
        )

    def test_validate_port(self):
        self.assertEqual(self.device.validate_port("dsl2:1_40"), ("dsl", 2))
        self.assertEqual(self.device.validate_port("port23"), ("dsl", 23))
        self.assertEqual(self.device.validate_port("ISKRATEL:sv-263-3443 atm 2/1"), ("dsl", 1))
        self.assertEqual(self.device.validate_port("24"), ("dsl", 24))
        self.assertEqual(self.device.validate_port("fasteth2"), ("fasteth", 2))
        self.assertEqual(self.device.validate_port("asd 1"), (None, None))

    def test_service_ports(self):
        self.assertListEqual(self.device._get_service_ports, ["1_32", "1_33", "1_40"])

    def test_get_mac_for_dsl_port(self):
        service_ports_length = len(self.device._get_service_ports)
        one_row = [("", "11:22:6E:89:8B:98")]
        # Для каждого сервис порта будут искаться MAC адреса
        # Так как в фейковой сессии прописан вывод на команду `show bridge mactable interface dsl`
        # То необходимо повторить данную строку столько раз, какое кол-во сервисных портов имеется
        valid_result = one_row * service_ports_length
        res = self.device.get_mac("3")
        self.assertListEqual(res, valid_result)

    def test_get_port_info(self):
        res = self.device.get_port_info("6")
        self.assertDictEqual(
            res,
            {
                "type": "adsl",
                "data": {
                    "profile_name": "N160-1856/608-6432AnnexM",
                    "first_col": ["Порт - UP", "Type                           ADSL2+ over POTS"],
                    "streams": [
                        {
                            "name": "Фактическая скорость передачи данных (Кбит/с)",
                            "down": {"color": "", "value": "6400"},
                            "up": {"color": "", "value": "928"},
                        },
                        {
                            "name": "Максимальная скорость передачи данных (Кбит/с)",
                            "down": {"color": "", "value": "8128"},
                            "up": {"color": "", "value": "1120"},
                        },
                        {
                            "name": "Сигнал/Шум (дБ)",
                            "down": {"color": "#95e522", "value": "13"},
                            "up": {"color": "#95e522", "value": "12"},
                        },
                        {
                            "name": "Interleaved channel delay (ms)",
                            "down": {"color": "", "value": "7"},
                            "up": {"color": "", "value": "7"},
                        },
                        {
                            "name": "Затухание линии (дБ)",
                            "down": {"color": "#95e522", "value": "34"},
                            "up": {"color": "#95e522", "value": "21"},
                        },
                    ],
                    "profiles": [
                        ("145", "N160-1856/608-6432AnnexM"),
                        ("139", "N160-928/608-4896Adsl2+"),
                        ("100", "N160/320ADSL2+"),
                    ],
                },
            },
        )
