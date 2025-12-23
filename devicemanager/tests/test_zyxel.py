import pathlib

from django.test import SimpleTestCase

from devicemanager.vendors.zyxel import Zyxel

from .base_factory_test import AbstractTestFactory

fake_auth = {"login": "test", "password": "password", "privilege_mode_password": ""}


class TestZyxelFactory(AbstractTestFactory):
    @staticmethod
    def get_device_class():
        return Zyxel

    @staticmethod
    def get_output_from_show_version_command() -> str:
        return """show: invalid command, valid commands are:
adsl            alarm           config          exit              
ip              statistics      switch          sys"""


class ZyxelPexpectFaker:
    """
    ## Это класс создает имитацию сессии pexpect для обработки команд Zyxel.
    """

    def __init__(self):
        self.before = b""
        self.sent_commands = []
        self.expect_cmd = 0

    def send(self, command: str):
        return self.sendline(command.strip())

    def sendline(self, command: str):
        self.sent_commands.append(command)

        if command == "config save":
            # Для случая 'OK'
            self.expect_cmd = 1

        elif command == "sys info show":
            self.before = b"""sys info show
         Hostname: DeviceName
         Location: 
          Contact: 
            Model: IES1248-51
    ZyNOS version: V3.53(ABQ.1) | 10/02/2009
         F/W size: 3027834
      MAC address: 00:11:22:33:44:55
   System up time: 368(days) :   13:32:24
 Bootbase version: VABQ1.01 | 02/07/2006
   F/W build date: Oct  2 2009 17:07:56
 DSP code version: 6.05.17
 Hardware version: A0B
    Serial number: 123456789
DeviceName>"""

        elif command == "statistics adsl show":
            self.before = b"""statistics adsl show
port status mode            up/downstream        up time error second(15M/24H)
---- ------ --------------- ------------- -------------- ---------------------
   1   -    -                    -/     -              -            -
   2   -    -                    -/     -              -            -
   3   -    -                    -/     -              -            -
   4   V    adsl2+            1146/ 25189 00000:00:39:58           0/0
   5   V    adsl2+(Annex M)   2518/ 25236 00015:20:43:39           4/20
   6   -    -                    -/     -              -            -
   7   -    -                    -/     -              -            -
   8   -    -                    -/     -              -            -
   9   -    -                    -/     -              -            -
  10   -    -                    -/     -              -            -
  11   -    -                    -/     -              -            -
  12   -    -                    -/     -              -            -
  13   V    adsl2+(Annex M)   1086/ 12496 00048:03:01:54           0/0
  14   -    -                    -/     -              -            -
  15   -    -                    -/     -              -            -
  16   -    -                    -/     -              -            -
  17   V    adsl2+(Annex M)   2453/ 25239 00008:00:33:07           0/0
  18   V    adsl2+(Annex M)   2369/ 24119 00034:07:34:51           0/0
  19   -    -                    -/     -              -            -
  20   -    -                    -/     -              -            -
  21   -    -                    -/     -              -            -
  22   -    -                    -/     -              -            -
  23   -    -                    -/     -              -            -
  24   V    adsl2+(Annex M)   2619/ 24867 00024:07:24:31           0/0
  25   -    -                    -/     -              -            -
  26   V    adsl2+(Annex M)   1086/ 12503 00000:01:09:31           0/73
  27   -    -                    -/     -              -            -
  28   -    -                    -/     -              -            -
  29   -    -                    -/     -              -            -
  30   -    -                    -/     -              -            -
  31   -    -                    -/     -              -            -
  32   -    -                    -/     -              -            -
  33   -    -                    -/     -              -            -
  34   V    adsl2+(Annex M)   2604/ 21133 00002:21:13:54           0/0
  35   V    adsl2+(Annex M)   2588/ 15240 00008:23:19:09           0/2
  36   -    -                    -/     -              -            -
  37   -    -                    -/     -              -            -
  38   -    -                    -/     -              -            -
  39   -    -                    -/     -              -            -
  40   -    -                    -/     -              -            -
  41   -    -                    -/     -              -            -
  42   -    -                    -/     -              -            -
  43   -    -                    -/     -              -            -
  44   -    -                    -/     -              -            -
  45   -    -                    -/     -              -            -
  46   -    -                    -/     -              -            -
  47   -    -                    -/     -              -            -
  48   -    -                    -/     -              -            -
DeviceName>"""

        elif command == "adsl show":
            self.before = b"""adsl show
port enable mode     up/downstream profile
---- ------ -------- ------------- -------------------------------
   1   V    auto       2976/ 24992 25-3Mb                         
   2   V    auto       2976/ 24992 25-3Mb                         
   3   V    auto       1024/  8160 8160-1024                      
   4   V    auto       2976/ 24992 25-3Mb                         
   5   V    auto       2976/ 24992 25-3Mb                         
   6   V    auto       2976/ 24992 25-3Mb                         
   7   V    auto       2976/ 24992 25-3Mb                         
   8   V    auto       2976/ 24992 25-3Mb                         
   9   V    auto       2976/ 24992 25-3Mb                         
  10   V    auto       2976/ 24992 25-3Mb                         
  11   V    auto       2976/ 24992 25-3Mb                         
  12   V    auto       2976/ 24992 25-3Mb                         
  13   V    auto       2976/ 24992 25-3Mb                         
  14   V    auto       2976/ 24992 25-3Mb                         
  15   V    auto       2976/ 24992 25-3Mb                         
  16   V    auto       2976/ 24992 25-3Mb                         
  17   V    auto       2976/ 24992 25-3Mb                         
  18   V    auto       2976/ 24992 25-3Mb                         
  19   V    auto       2976/ 24992 25-3Mb                         
  20   V    auto       2976/ 24992 25-3Mb                         
  21   V    auto       2976/ 24992 25-3Mb                         
  22   V    auto       2976/ 24992 25-3Mb                         
  23   V    auto       2976/ 24992 25-3Mb                         
  24   V    auto       2976/ 24992 25-3Mb                         
  25   V    auto       2976/ 24992 25-3Mb                         
  26   V    auto       2976/ 24992 25-3Mb                         
  27   V    auto       2976/ 24992 25-3Mb                         
  28   V    auto       2976/ 24992 25-3Mb                         
  29   V    auto       2976/ 24992 25-3Mb                         
  30   V    auto       2976/ 24992 25-3Mb                         
  31   V    auto       2976/ 24992 25-3Mb                         
  32   V    auto       2976/ 24992 25-3Mb                         
  33   V    auto       2976/ 24992 25-3Mb                         
  34   V    auto       2976/ 24992 25-3Mb                         
  35   V    auto       2976/ 24992 25-3Mb                         
  36   V    auto       2976/ 24992 25-3Mb                         
  37   V    auto       2976/ 24992 25-3Mb                         
  38   V    auto       2976/ 24992 25-3Mb                         
  39   V    auto       2976/ 24992 25-3Mb                         
  40   V    auto       2976/ 24992 25-3Mb                         
  41   V    auto       2976/ 24992 25-3Mb                         
  42   V    auto       2976/ 24992 25-3Mb                         
  43   V    auto       2976/ 24992 25-3Mb                         
  44   V    auto       2976/ 24992 25-3Mb                         
  45   V    auto       2976/ 24992 25-3Mb                         
  46   V    auto       2976/ 24992 25-3Mb                         
  47   V    auto       2976/ 24992 25-3Mb                         
  48   V    auto       2976/ 24992 25-3Mb                         

Subscriber Info:
port name                             tel
---- -------------------------------- ----------------
   1 -                                -
   2 -                                -
   3 -                                -
   4 -                                -
   5 -                                -
   6 -                                -
   7 -                                -
   8 -                                -
   9 -                                -
  10 -                                -
  11 -                                -
  12 -                                -
  13 -                                -
  14 -                                -
  15 -                                -
  16 -                                -
  17 -                                -
  18 -                                -
  19 -                                -
  20 -                                -
  21 -                                -
  22 -                                -
  23 -                                -
  24 -                                -
  25 -                                -
  26 -                                -
  27 -                                -
  28 -                                -
  29 -                                -
  30 -                                -
  31 -                                -
  32 -                                -
  33 desc                             -
  34 -                                -
  35 -                                -
  36 -                                -
  37 -                                -
  38 -                                -
  39 -                                -
  40 -                                -
  41 -                                -
  42 -                                -
  43 -                                -
  44 -                                -
  45 -                                -
  46 -                                -
  47 -                                -
  48 -                                -
DeviceName>"""

        elif command == "statistics enet show":
            self.before = b"""statistics enet show
 port  status   mode             duplex             up time
----- --------- ---------------- ----------- --------------
enet1 link up   1000copper       full duplex 00368:13:35:14
enet2 disabled  -                -                        -
DeviceName>"""

        elif command == "switch enet show":
            self.before = b"""switch enet show
 port mode             name
----- ---------------- -------------------------------
enet1 auto             uplink
enet2 disabled         
DeviceName>"""

        elif command == "statistics vlan":
            self.before = b"""statistics vlan
 vid name             F:fixed X:forbidden N:normal   U:untag T:tag    E:egress
---- ---------------- --------------------------------------------------------
 101 -
     static           123456789012345678901234567890123456789012345678 12
                      XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX FF
                      ------------------------------------------------ TT
                      ------------------------------------------------ EE
 106 -
     static           123456789012345678901234567890123456789012345678 12
                      XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX FF
                      ------------------------------------------------ TT
                      ------------------------------------------------ EE
 110 -
     static           123456789012345678901234567890123456789012345678 12
                      XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX FF
                      ------------------------------------------------ TT
                      ------------------------------------------------ EE
 400 -
     static           123456789012345678901234567890123456789012345678 12
                      XXXXXXXXXXFXXXXXXXXXXXXXXXXXXXFXXXXXXXXXXXXXXXXX FF
                      ----------U-------------------U----------------- TT
                      ----------E-------------------E----------------- EE
 719 -
     static           123456789012345678901234567890123456789012345678 12
                      FFFFFFFFFFXFFFFFFFFFFFFFFFFFFFXFFFFFFFFFFFFFFFFF FF
                      UUUUUUUUUU-UUUUUUUUUUUUUUUUUUU-UUUUUUUUUUUUUUUUU TT
                      EEEEEEEEEE-EEEEEEEEEEEEEEEEEEE-EEEEEEEEEEEEEEEEE EE
DeviceName>"""

        elif "statistics mac" in command:
            self.before = b"""statistics mac 13
Port: 13
index  vid mac
----- ---- -----------------
    1  719 11:22:33:44:55:aa
    2  719 11:22:33:44:55:bb
    3  719 11:22:33:44:55:cc
DeviceName>"""

        elif command == "adsl profile show":
            self.before = b"""adsl profile show
01. 1024-256      latency mode: interleave
                       up stream down stream
                       --------- -----------
max rate       (kbps):       256        1024
min rate       (kbps):        32          64
latency delay    (ms):         4           4
max margin       (db):        31          31
min margin       (db):         0           0
target margin    (db):         6           6
up   shift margin(db):         9           9
down shift margin(db):         3           3

02. 11500-1056      latency mode: interleave
                       up stream down stream
                       --------- -----------
max rate       (kbps):      1056       11500
min rate       (kbps):        32          64
latency delay    (ms):        20          20
max margin       (db):        31          31
min margin       (db):         0           0
target margin    (db):         8           8
up   shift margin(db):         9           9
down shift margin(db):         3           3
DeviceName>"""

        elif "adsl show" in command:
            self.before = b"""adsl show 3
port enable mode     up/downstream profile
---- ------ -------- ------------- -------------------------------
   3   V    auto       1024/  8160 8160-1024                      

Subscriber Info:
port name                             tel
---- -------------------------------- ----------------
   3 -                                -
DeviceName>"""

        elif "statistics adsl linerate" in command:
            self.before = b"""statistics adsl linerate 13
[port 13]
AS0 downstream rate            (kbps): 12496
LS0 upstream   rate            (kbps):  1086
down/up stream margin            (db): 24.0/25.1
down/up stream attenuation       (db):     6.2/   14.0
attainable down/up stream rate (kbps): 15288/ 2444

DeviceName>"""

        else:
            self.before = b""
        return len(command)

    def expect(self, *args, **kwargs):
        if self.expect_cmd != 0:
            # Если указан другой случай ожидания, то выдаем его и снова ставим по умолчанию `0`
            v = self.expect_cmd
            self.expect_cmd = 0
            return v

        return 0


class TestZyxelInit(SimpleTestCase):
    def test_initial_data(self):
        zyxel = Zyxel(session=ZyxelPexpectFaker(), ip="10.10.10.10", auth=fake_auth)

        self.assertEqual(zyxel.mac, "00:11:22:33:44:55")
        self.assertEqual(zyxel.serialno, "123456789")
        self.assertEqual(zyxel.model, "IES1248-51")


class TestZyxelInterfaces(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TEMPLATE_DIR = pathlib.Path(__file__).parent.parent / "templates"
        # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса Zyxel.
        fake_session = ZyxelPexpectFaker()
        # Создание объекта Zyxel с fake_session, ip-адресом и авторизацией.
        cls.zyxel = Zyxel(fake_session, "10.10.10.10", auth=fake_auth)

    def test_get_interfaces(self):
        # Получение интерфейсов от объекта zyxel.
        interfaces = self.zyxel.get_interfaces()
        print(interfaces)
        self.assertEqual(
            interfaces,
            [
                ("1", "down", ""),
                ("2", "down", ""),
                ("3", "down", ""),
                ("4", "up", ""),
                ("5", "up", ""),
                ("6", "down", ""),
                ("7", "down", ""),
                ("8", "down", ""),
                ("9", "down", ""),
                ("10", "down", ""),
                ("11", "down", ""),
                ("12", "down", ""),
                ("13", "up", ""),
                ("14", "down", ""),
                ("15", "down", ""),
                ("16", "down", ""),
                ("17", "up", ""),
                ("18", "up", ""),
                ("19", "down", ""),
                ("20", "down", ""),
                ("21", "down", ""),
                ("22", "down", ""),
                ("23", "down", ""),
                ("24", "up", ""),
                ("25", "down", ""),
                ("26", "up", ""),
                ("27", "down", ""),
                ("28", "down", ""),
                ("29", "down", ""),
                ("30", "down", ""),
                ("31", "down", ""),
                ("32", "down", ""),
                ("33", "down", "desc"),
                ("34", "up", ""),
                ("35", "up", ""),
                ("36", "down", ""),
                ("37", "down", ""),
                ("38", "down", ""),
                ("39", "down", ""),
                ("40", "down", ""),
                ("41", "down", ""),
                ("42", "down", ""),
                ("43", "down", ""),
                ("44", "down", ""),
                ("45", "down", ""),
                ("46", "down", ""),
                ("47", "down", ""),
                ("48", "down", ""),
                ("enet1", "up", "uplink"),
                ("enet2", "admin down", ""),
            ],
        )

    def test_get_vlans(self):
        # Получение интерфейсов и VLAN от объекта zyxel.
        interfaces_vlans = self.zyxel.get_vlans()
        print(interfaces_vlans)
        self.assertEqual(
            interfaces_vlans,
            [
                ("1", "down", "", [719]),
                ("2", "down", "", [719]),
                ("3", "down", "", [719]),
                ("4", "up", "", [719]),
                ("5", "up", "", [719]),
                ("6", "down", "", [719]),
                ("7", "down", "", [719]),
                ("8", "down", "", [719]),
                ("9", "down", "", [719]),
                ("10", "down", "", [719]),
                ("11", "down", "", [400]),
                ("12", "down", "", [719]),
                ("13", "up", "", [719]),
                ("14", "down", "", [719]),
                ("15", "down", "", [719]),
                ("16", "down", "", [719]),
                ("17", "up", "", [719]),
                ("18", "up", "", [719]),
                ("19", "down", "", [719]),
                ("20", "down", "", [719]),
                ("21", "down", "", [719]),
                ("22", "down", "", [719]),
                ("23", "down", "", [719]),
                ("24", "up", "", [719]),
                ("25", "down", "", [719]),
                ("26", "up", "", [719]),
                ("27", "down", "", [719]),
                ("28", "down", "", [719]),
                ("29", "down", "", [719]),
                ("30", "down", "", [719]),
                ("31", "down", "", [400]),
                ("32", "down", "", [719]),
                ("33", "down", "desc", [719]),
                ("34", "up", "", [719]),
                ("35", "up", "", [719]),
                ("36", "down", "", [719]),
                ("37", "down", "", [719]),
                ("38", "down", "", [719]),
                ("39", "down", "", [719]),
                ("40", "down", "", [719]),
                ("41", "down", "", [719]),
                ("42", "down", "", [719]),
                ("43", "down", "", [719]),
                ("44", "down", "", [719]),
                ("45", "down", "", [719]),
                ("46", "down", "", [719]),
                ("47", "down", "", [719]),
                ("48", "down", "", [719]),
                ("enet1", "up", "uplink", [101, 106, 110, 400, 719]),
                ("enet2", "admin down", "", [101, 106, 110, 400, 719]),
            ],
        )


class TestZyxelGetMACAddress(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса Zyxel.
        fake_session = ZyxelPexpectFaker()
        # Создание объекта Zyxel с fake_session, ip-адресом и авторизацией.
        cls.zyxel = Zyxel(fake_session, "10.10.10.10", auth=fake_auth)

    def test_get_mac(self):
        mac_list = self.zyxel.get_mac("enet1")

        self.assertEqual(
            mac_list,
            [(719, "11:22:33:44:55:aa"), (719, "11:22:33:44:55:bb"), (719, "11:22:33:44:55:cc")],
        )


class TestZyxelPortControl(SimpleTestCase):
    # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса Zyxel.
    fake_session = ZyxelPexpectFaker()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создание объекта Zyxel с fake_session, ip-адресом и авторизацией.
        cls.zyxel = Zyxel(cls.fake_session, "10.10.10.10", auth=fake_auth)

    def setUp(self) -> None:
        self.fake_session.sent_commands = []

    def test_reload_port(self):
        self.zyxel.reload_port("1")

        self.assertEqual(
            self.fake_session.sent_commands,
            ["adsl disable 1", "adsl enable 1", "config save"],
        )

    def test_reload_port_no_save(self):
        self.zyxel.reload_port("1", save_config=False)

        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "adsl disable 1",
                "adsl enable 1",
            ],
        )

    def test_reload_invalid_port(self):
        status = self.zyxel.reload_port("0/1")

        self.assertEqual(status, "Неверный порт")

        self.assertEqual(
            self.fake_session.sent_commands,
            [],
        )

    def test_set_up_port(self):
        self.zyxel.set_port("enet1", "up")

        self.assertEqual(
            self.fake_session.sent_commands,
            ["switch enet enable enet1", "config save"],
        )

    def test_set_up_port_no_save(self):
        # Установка порта Te 0/1/2 на up.
        self.zyxel.set_port("enet1", "up", save_config=False)

        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "switch enet enable enet1",
            ],
        )

    def test_set_up_invalid_port(self):
        status = self.zyxel.set_port("1/2", "up")

        self.assertEqual(status, "Неверный порт")

        self.assertEqual(
            self.fake_session.sent_commands,
            [],
        )

    def test_set_down_port(self):
        self.zyxel.set_port("enet2", "down")

        self.assertEqual(
            self.fake_session.sent_commands,
            ["switch enet disable enet2", "config save"],
        )

    def test_set_down_invalid_port(self):
        status = self.zyxel.set_port("0/2", "down")

        self.assertEqual(status, "Неверный порт")

        self.assertEqual(
            self.fake_session.sent_commands,
            [],
        )


class TestZyxelInfo(SimpleTestCase):
    # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса Zyxel.
    fake_session = ZyxelPexpectFaker()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создание объекта Zyxel с fake_session, ip-адресом и авторизацией.
        cls.zyxel = Zyxel(cls.fake_session, "10.10.10.10", auth=fake_auth)

    def setUp(self) -> None:
        self.fake_session.sent_commands = []

    def test_get_port_info(self):
        value = self.zyxel.get_port_info("1")
        # print(value)

        self.assertEqual(value["data"]["profile_name"], "8160-1024")
        self.assertEqual(value["data"]["port"], "1")
        self.assertListEqual(value["data"]["profiles"], [("01", "1024-256"), ("02", "11500-1056")])

        # Имеются 4 строки данных.
        self.assertEqual(len(value["data"]["streams"]), 4)

        # Смотрим что все значения получены.
        self.assertTrue(all(map(lambda x: x["up"]["value"] > 0, value["data"]["streams"])))
        self.assertTrue(all(map(lambda x: x["down"]["value"] > 0, value["data"]["streams"])))

    def test_invalid_get_port_info(self):
        status = self.zyxel.get_port_info(port="Re 0/1")

        self.assertEqual({"type": "error", "data": "Неверный порт"}, status)

        self.assertEqual(self.fake_session.sent_commands, [])


class TestZyxelPortDescription(SimpleTestCase):
    # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса Zyxel.
    fake_session = ZyxelPexpectFaker()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создание объекта Zyxel с fake_session, ip-адресом и авторизацией.
        cls.zyxel = Zyxel(cls.fake_session, "10.10.10.10", auth=fake_auth)

    def setUp(self) -> None:
        self.fake_session.sent_commands = []

    def test_change_description(self):
        self.zyxel.set_description("enet2", "New [desc] \nновое описание")
        self.assertEqual(
            self.fake_session.sent_commands,
            [
                'switch enet name enet2 "New_(desc)_novoe_opisanie"',
                "config save",
            ],
        )

    def test_change_description_adsl(self):
        self.zyxel.set_description("1", "New [desc] \nновое описание")
        self.assertEqual(
            self.fake_session.sent_commands,
            [
                'adsl name 1 "New_(desc)_novoe_opisanie"',
                "config save",
            ],
        )

    def test_clear_description(self):
        self.zyxel.set_description("enet2", "")
        self.assertEqual(
            self.fake_session.sent_commands,
            [
                'switch enet name enet2 ""',
                "config save",
            ],
        )

    def test_clear_description_adsl(self):
        self.zyxel.set_description("2", "")
        self.assertEqual(
            self.fake_session.sent_commands,
            [
                'adsl name 2 ""',
                "config save",
            ],
        )
