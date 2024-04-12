from django.test import SimpleTestCase

from devicemanager.vendors.almatek import Almatek
from .base_factory_test import AbstractTestFactory

fake_auth = {"login": "test", "password": "password", "privilege_mode_password": ""}


class TestAlmatekFactory(AbstractTestFactory):
    @staticmethod
    def get_device_class():
        return Almatek

    @staticmethod
    def get_output_from_show_version_command() -> str:
        return """
Loader Version   : 3.6.7.55090\r\nLoader Date      : Jun 29 2023 - 07:35:14\n
Firmware Version : 1.0.0.16\r\nFirmware Date     : Jun 29 2023 - 07:36:51\r\n"""


class AlmatekPexpectFaker:
    """
    ## Это класс создает имитацию сессии pexpect для обработки команд Cisco.
    """

    def __init__(self):
        self.before = b""
        self.sent_commands = []
        self.expect_cmd = 0

    def send(self, command: str):
        return self.sendline(command.strip())

    def expect(self, *args, **kwargs):
        if self.expect_cmd != 0:
            # Если указан другой случай ожидания, то выдаем его и снова ставим по умолчанию `0`
            v = self.expect_cmd
            self.expect_cmd = 0
            return v

        return 0

    def sendline(self, command: str):
        self.sent_commands.append(command)

        if command == "show info":
            self.before = b"""
System Model       : AN-SGM10P8A
System Name        : GO248A-KSPI-CAMS-ASW3
System Location    : GO248A
System Contact     : Default
System SN          : AN-SGM10P8A-1023-039
MAC Address        : 00:E0:53:17:E6:36
Default IP Address : 0.0.0.0
Subnet Mask        : 0.0.0.0
Loader Version     : 3.6.7.55090
Loader Date        : Jun 29 2023 - 07:35:14
Firmware Version   : 1.0.0.16
Firmware Date      : Jun 29 2023 - 07:36:51
System Object ID   : 1.3.6.1.4.1.27282.1.1
System Up Time     : 1 days, 22 hours, 13 mins, 59 secs
"""

        elif command == "show interfaces brief":
            self.before = b"""Port    Name              Status      Pvid   Duplex    Speed          Type
gi1     desc1             connect     3929   a-full    a-100M         Copper
gi2                       connect     3929   a-full    a-100M         Copper
gi3                       connect     3929   a-full    a-100M         Copper
gi4                       connect     3929   a-full    a-100M         Copper
gi5                       connect     3929   a-full    a-100M         Copper
gi6                       connect     3929   a-full    a-100M         Copper
gi7                       disable     3929   auto      auto           Copper
gi8                       notconnect  1      auto      auto           Copper
gi9                       connect     1      a-full    a-1000M        Fiber
gi10                      notconnect  1      auto      auto           Fiber
"""
        elif command == "show vlan":
            self.before = b"""
VID  VLAN Name        Untagged Ports              Tagged Ports                Type
1    default          gi8-10,lag1-8                                           Default
3000 NAME             gi1-7                       gi8-9                       Static
"""
        elif command == "show mac address-table interface GigabitEthernet 1":
            self.before = b"""
 VID  | MAC Address       | Type              | Ports          
------+-------------------+-------------------+----------------
 3929 | 00:E0:53:17:E6:36 | Management        | CPU 
 3929 | 80:BE:AF:52:B3:F8 | Dynamic           | gi1 

Total number of entries: 2
"""
        elif command == "show interface GigabitEthernet 1":
            self.before = b"""
GigabitEthernet1 is up
  Hardware is Gigabit Ethernet
  Auto-duplex, Auto-speed, media type is Copper
  back-pressure is enabled
     40580004 packets input, 56466574194 bytes, 3 discarded packets
     595 broadcasts  1515 multicasts 40577894 unicasts
     0 runts, 0 giants, 0 discarded event packets
     0 input errors, 0 CRC, 0 frame
     1515 multicast, 0 pause input
     0 input packets with dribble condition detected
     last 5 minutes input rate 4102648 bits/sec, 359 packets/sec

     21421365 packets output, 1820844530 bytes, 0 discarded packets
     258565 broadcasts  2232732 multicasts 18930068 unicasts
     0 output errors, 0 collisions
     0 babbles, 0 late collision, 0 deferred
     0 PAUSE output
     last 5 minutes output rate 133712 bits/sec, 188 packets/sec
"""


class TestAlmatekInit(SimpleTestCase):
    def test_initial_data(self):
        almatek = Almatek(session=AlmatekPexpectFaker(), ip="10.10.10.10", auth=fake_auth)

        self.assertEqual(almatek.model, "AN-SGM10P8A")
        self.assertEqual(almatek.mac, "00:E0:53:17:E6:36")
        self.assertEqual(almatek.serialno, "AN-SGM10P8A-1023-039")


class TestAlmatekInterfaces(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса Cisco.
        fake_session = AlmatekPexpectFaker()
        # Создание объекта Cisco с fake_session, ip-адресом и авторизацией.
        cls.almatek = Almatek(fake_session, "10.10.10.10", auth=fake_auth)

    def test_get_interfaces(self):
        # Получение интерфейсов от объекта Almatek.
        interfaces = self.almatek.get_interfaces()
        self.assertEqual(
            interfaces,
            [
                ("gi1", "up", "desc1"),
                ("gi2", "up", ""),
                ("gi3", "up", ""),
                ("gi4", "up", ""),
                ("gi5", "up", ""),
                ("gi6", "up", ""),
                ("gi7", "admin down", ""),
                ("gi8", "down", ""),
                ("gi9", "up", ""),
                ("gi10", "down", ""),
            ],
        )

    def test_get_vlans(self):
        # Получение интерфейсов от объекта Almatek.
        interfaces = self.almatek.get_vlans()
        self.assertEqual(
            interfaces,
            [
                ("gi1", "up", "desc1", [3000]),
                ("gi2", "up", "", [3000]),
                ("gi3", "up", "", [3000]),
                ("gi4", "up", "", [3000]),
                ("gi5", "up", "", [3000]),
                ("gi6", "up", "", [3000]),
                ("gi7", "admin down", "", [3000]),
                ("gi8", "down", "", [1, 3000]),
                ("gi9", "up", "", [1, 3000]),
                ("gi10", "down", "", [1]),
            ],
        )

    def test_get_macs(self):
        mac_list = self.almatek.get_mac("gi1")
        self.assertEqual(mac_list, [(3929, "80:BE:AF:52:B3:F8")])

        mac_list_2 = self.almatek.get_mac("rea0/1")
        self.assertEqual(mac_list_2, [])
