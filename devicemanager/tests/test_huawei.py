import re
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from devicemanager.vendors import Huawei, HuaweiMA5600T
from .base_factory_test import AbstractTestFactory
from ..multifactory import DeviceMultiFactory


class TestHuaweiS2403TPFactory(AbstractTestFactory):
    @staticmethod
    def get_device_class():
        return Huawei

    @staticmethod
    def get_output_from_show_version_command() -> str:
        """
        Huawei не имеют команду `show version` и возвращают данную строку
        """
        return """
              ^
Error: Unrecognized command found at '^' position.
"""

    @staticmethod
    def get_output_from_display_version_command():
        """
        HuaweiFactory вызывает еще одну команду `display version`, перехватываем её и возвращаем
        данную строку, для `S2403TP-EA` без доступа нельзя посмотреть, поэтому он выдает следующую строку.
        """
        return """
                        ^
 % Unrecognized command found at '^' position."""

    @patch("devicemanager.vendors.huawei.factory.HuaweiFactory.send_command")
    def test_factory_return_class(self, huawei_factory_send_command: Mock):
        huawei_factory_send_command.return_value = self.get_output_from_display_version_command()
        super().test_factory_return_class()

    @patch("devicemanager.vendors.huawei.factory.HuaweiFactory.send_command")
    def test_factory_device_attributes(self, huawei_factory_send_command: Mock):
        huawei_factory_send_command.return_value = self.get_output_from_display_version_command()
        super().test_factory_device_attributes()


class TestHuaweiS2326TPFactory(TestHuaweiS2403TPFactory):
    @staticmethod
    def get_output_from_display_version_command():
        """
        HuaweiFactory вызывает еще одну команду `display version`, перехватываем её и возвращаем
        данную строку, для `S2326TP-EI` без доступа нельзя посмотреть, поэтому он выдает следующую строку.
        """
        return """
Huawei Versatile Routing Platform Software
VRP (R) software, Version 5.70 (S2300 V100R006C05)
Copyright (C) 2003-2013 HUAWEI TECH CO., LTD
Quidway S2326TP-EI Routing Switch uptime is 6 weeks, 2 days, 0 hour, 41 minutes

EFFE 0(Master) : uptime is 6 weeks, 2 days, 0 hour, 41 minutes
64M bytes DDR Memory
16M bytes FLASH
Pcb      Version :  VER C
Basic  BOOTROM  Version :  149 Compiled at Mar 15 2013, 11:02:25
Software Version : VRP (R) Software, Version 5.70 (V100R006C05)"""


class FakeHuaweiMA5600TSession:
    def __init__(self):
        self._output = b""

    @staticmethod
    def expect(*args, **kwargs):
        return 0

    @property
    def before(self) -> bytes:
        return self._output

    def send(self, command, *args, **kwargs):
        return self.sendline(command, *args, **kwargs)

    def sendline(self, command: str, *args, **kwargs):
        if command == "display version":
            self._output = b"""
{ <cr>|backplane<K>|frameid/slotid<S><Length 1-15> }:

  Command:
          display version

  VERSION : MA5600V800R007C00
  PATCH   : SPC300 SPH327 HP3008 HP3030
  PRODUCT MA5600T
  Uptime is 376 day(s), 15 hour(s), 31 minute(s), 11 second(s)"""

        elif command == "display adsl line-profile\n\n":
            # ADSL
            self._output = b"""
       31 N160-1856/ G.992.5     Interleaved       608      6432     160    1856
          608-6432An
          nexM
       32 N320-2464/ G.992.5     Interleaved      2464     12896     160    2464
          2464-12896
          AnnexM
       33 N608-3008/ G.992.5     Interleaved      4896     18720     608    3008
          4896-18720
          AnnexM
     1000 ADSL LINE  All         Fast               32      6144      32     640
          PROFILE 10
          00
  ------------------------------------------------------------------------------
  Total:      40
  Note :      The unit of rate is Kbps"""

        elif command == "display vdsl line-template info\n":
            # VDSL
            self._output = b"""
Template  Template
Index     Name
------------------------------
       1  DEFVAL
       2  VDSL LINE TEMPLATE 2
       3  VDSL LINE TEMPLATE 3
       4  NO_CHANGE
       5  VDSL
"""
        elif "display board" in command:
            self._output = b"""
#------------------------------------------------------------------------
SlotID  BoardName  Status         SubType0 SubType1    Online/Offline
#------------------------------------------------------------------------
0
1
2       H808ADLF   Normal
3       H808ADLF   Normal
4       H808ADLF   Normal
5       H808ADLF   Normal
6       H808ADLF   Normal
7
8       H805ADPD   Normal
9       H801SCUB   Active_normal
10      H801GI     Active_normal
"""
        elif "display current-configuration ont" in command:
            # GPON
            self._output = b"""config
line1
line2
line3"""
        elif "display ont info summary" in command:
            # GPON
            self._output = b"""  Command is being executed. Please wait
  ------------------------------------------------------------------------------
  In port 0/1/1, the total of ONTs are: 5, online: 4
  ------------------------------------------------------------------------------
  ONT  Run     Last                Last                Last
  ID   State   UpTime              DownTime            DownCause
  ------------------------------------------------------------------------------
  0    online  2023-07-15 04:11:34 2023-07-15 03:50:13 dying-gasp
  1    offline -                   -                   -
  2    online  2023-09-03 19:12:20 2023-08-29 01:15:16 dying-gasp
  3    online  2023-09-08 20:34:45 2023-09-02 20:35:31 dying-gasp
  4    online  2023-07-15 04:11:58 2023-07-15 03:50:13 dying-gasp
  ------------------------------------------------------------------------------
  ONT        SN        Type          Distance Rx/Tx power  Description
  ID                                    (m)      (dBm)
  ------------------------------------------------------------------------------
  0   48575443E754CA71 245H             2171  -22.84/2.01  POR40/11_kv3_Kasjanov
  1   48575443E768B671 -                -     -/-          POR40/1_kv14_TushevaL
  2   48575443E755DA71 245H             2166  -21.61/2.14  POR40/11_kv54_Polishu
  3   4857544359DB3037 245H             2155  -20.75/2.06  POR40/11_kv66_Semenov
  4   485754438A8F3345 245H             2170  -22.52/2.42  POR40/11_kv48_Kondyak
"""
        elif "display line operation" in command:
            # VDSL
            self._output = b"""
  ------------------------------------------------------------------------------
  Standard in port training                  : G.992.5-Annex M
  Current power management state             : Full-on state
  Result of the last full initialization     : No failure
  G.998.4 retransmission used downstream     : Unused, retransmission mode is
                                               forbidden
  G.998.4 retransmission used upstream       : Unused, retransmission mode is
                                               forbidden
  Signal attenuation downstream(dB)          : 0.9
  Signal attenuation upstream(dB)            : 8.0
  Line attenuation downstream(dB)            : 6.5
  Line attenuation upstream(dB)              : 10.4
  Maximum attainable rate downstream(Kbps)   : 25520
  Maximum attainable rate upstream(Kbps)     : 1319
  Actual line rate downstream(Kbps)          : 25580
  Actual line rate upstream(Kbps)            : 1396
  Line SNR margin downstream(dB)             : 7.2
  Line SNR margin upstream(dB)               : 7.7
  Actual PSD downstream(dBm/Hz)              : -43.1
  Actual PSD upstream(dBm/Hz)                : -40.4
  Highest frequency downstream(kHz)          : 2203.69
  Lowest frequency downstream(kHz)           : 276.00
  Highest frequency upstream(kHz)            : 138.00
  Lowest frequency upstream(kHz)             : 30.19
  Actual KL0_CO value(0.1dB)                 : -
  Actual KL0_CPE value(0.1dB)                : -
  Total output power downstream(dBm)         : 17.3
  Total output power upstream(dBm)           : 9.8
  Current VDSL2 profile                      : -
  Coding gain in downstream(dB)              : -
  Coding gain in upstream(dB)                : -
  Power cut back downstream(dB)              : -
  Actual limit PSD mask                      : -
  Actual transmit rate adaptation downstream : AdaptAtStartup
  Actual transmit rate adaptation upstream   : AdaptAtStartup
  Actual INP of ROC downstream (DMT symbol)  : -
  Actual INP of ROC upstream (DMT symbol)    : -
  Actual SNR margin of ROC downstream(dB)    : -
  Actual SNR margin of ROC upstream(dB)      : -
  ------------------------------------------------------------------------------
  Note: The 102.3 dB signal attenuation, 102.3 dB line attenuation,
  -51.2 dB SNR margin, and 204.7 dB KL0 value indicate that the
  parameters are not within their specified ranges."""

        elif command == "y\n":
            # Для ADSL port info, после подтверждения команды `display line operation`
            self._output = b"""
  Channel mode                              : Interleaved
  Downstream channel bit swap               : Enable
  Upstream channel bit swap                 : Enable
  Trellis mode                              : Enable
  Standard in port training                 : G992.5-Annex A
  Downstream actual net data rate(Kbps)     : 12887
  Downstream max. attainable rate(Kbps)     : 15666
  Downstream channel SNR margin(dB)         : 14.8
  Downstream interleaved channel delay(ms)  : 5
  Downstream channel attenuation(dB)        : 16.5
  Downstream total output power(dBm)        : 2.0
  Upstream actual net data rate(Kbps)       : 1052
  Upstream max. attainable rate(Kbps)       : 1247
  Upstream channel SNR margin(dB)           : 10.2
  Upstream interleaved channel delay(ms)    : 7
  Upstream channel attenuation(dB)          : 8.6
  Upstream total output power(dBm)          : 6.3
  Current power management state            : Full-on state
  ------------------------------------------------------------------------
  G.992.1 : G.dmt
  G.992.2 : G.lite
  G.992.3 : G.dmt.bis
  G.992.5 : G.dmt.bisplus
"""
        elif re.match(r"display port state 4", command):
            # ADSL
            self._output = b"""
------------------------------------------------------------------------
  Port         Status           Line_Profile   Alm_Profile   Ext_Profile
  ------------------------------------------------------------------------
     4         Activated                  32             1            --
  ------------------------------------------------------------------------"""

        elif re.match(r"display port state 17", command):
            # VDSL
            self._output = b"""
  ------------------------------------------------------------------------------
  Port   Status        Loopback        Line Template   Alarm Template  Group ID
  ------------------------------------------------------------------------------
     1   Activated     Disable                     2                1         -
  ------------------------------------------------------------------------------
"""

        elif re.match(r"^display adsl line-profile \d+", command):
            # ADSL
            self._output = b"""
  ------------------------------------------------------------------------------
  
  Profile index :32   Name: N320-2464/2464-12896AnnexM
  ADSL transmission mode                        : G.992.5
  Trellis mode                                  : Enable
  Upstream channel bit swap                     : Enable
  Downstream channel bit swap                   : Enable
  Channel mode                                  : Interleaved
  Maximum downstream interleaved delay(ms)      : 8
  Maximum upstream interleaved delay(ms)        : 8
  Target downstream SNR margin(dB)              : 10
  Maximum acceptable downstream SNR margin(dB)  : 20
  Minimum acceptable downstream SNR margin(dB)  : 0
  Target upstream SNR margin(dB)                : 10
  Maximum acceptable upstream SNR margin(dB)    : 20
  Minimum acceptable upstream SNR margin(dB)    : 0
  Downstream SNR margin for rate downshift(dB)  : 7
  Downstream SNR margin for rate upshift(dB)    : 13
  Upstream SNR margin for rate downshift(dB)    : 7
  Upstream SNR margin for rate upshift(dB)      : 13
  Minimum upshift time in downstream(seconds)   : 60
  Minimum downshift time in downstream(seconds) : 60
  Minimum upshift time in upstream(seconds)     : 60
  Minimum downshift time in upstream(seconds)   : 60
  Downstream form of transmit rate adaptation   : Adapting at runtime
  Minimum transmit rate downstream(Kbps)        : 2464
  Maximum transmit rate downstream(Kbps)        : 12896
  Minimum transmit rate upstream(Kbps)          : 160
  Maximum transmit rate upstream(Kbps)          : 2464
  ------------------------------------------------------------------------------
"""
        elif re.search("display\s+mac-address\s+port", command):
            self._output = b"""
   SRV-P BUNDLE TYPE MAC            MAC TYPE F /S /P  VPI  VCI   VLAN ID
   INDEX INDEX
   ---------------------------------------------------------------------
     689    -   adl  9afc-8d4c-1525 dynamic  0 /3 /27 1    33    1418
     689    -   adl  e0cc-f85d-3818 dynamic  0 /11/27 1    33    1418
     690    -   adl  bc76-706c-c671 dynamic  0 /11/27 1    40    704
   ---------------------------------------------------------------------
"""
        elif re.search("display\s+security\s+bind\s+mac", command):
            self._output = b"""
   Index     MAC-Address FlowID  F/ S/ P   VLAN-ID  Vpi  Vci FlowType    FlowPara
   ------------------------------------------------------------------------------
       0  0002-cf93-db80    879  0 /2 /15      735    1   40        -           -
       0  0a31-92f7-1625    582  0 /11/16      707    1   40        -           -"""


class TestHuaweiMA5600TFactory(AbstractTestFactory):
    def setUp(self) -> None:
        super().setUp()
        self.vdsl_templates = [
            ("5", "VDSL"),
            ("4", "NO_CHANGE"),
            ("3", "VDSL LINE TEMPLATE 3"),
            ("2", "VDSL LINE TEMPLATE 2"),
            ("1", "DEFVAL"),
        ]

    @staticmethod
    def get_device_class():
        return HuaweiMA5600T

    @staticmethod
    def get_output_from_show_version_command() -> str:
        return """
                        ^
  % Unknown command, the error locates at '^'
"""

    @staticmethod
    def get_fake_session():
        return FakeHuaweiMA5600TSession()

    @patch("devicemanager.multifactory.DeviceMultiFactory.send_command")
    def test_device_extra_attributes(self, send_command: Mock):
        if self._is_need_skip():
            return

        send_command.return_value = self.version_output

        device = DeviceMultiFactory.get_device(
            session=self.fake_session,
            ip="10.10.10.10",
            snmp_community="",
            auth=self.auth_dict,
        )
        self.assertTrue(hasattr(device, "vdsl_templates"))
        self.assertTrue(hasattr(device, "adsl_profiles"))
        self.assertTrue(hasattr(device, "interfaces"))
        self.assertTrue(hasattr(device, "interfaces_vlans"))
        self.assertEqual(getattr(device, "vdsl_templates"), self.vdsl_templates)


class TestHuaweiMA5600T(SimpleTestCase):
    def setUp(self) -> None:
        self.device = HuaweiMA5600T(
            session=FakeHuaweiMA5600TSession(),
            ip="10.10.10.10",
            snmp_community="",
            auth={
                "login": "user",
                "password": "passwd",
                "privilege_mode_password": "secret",
            },
        )

    def test_port_split(self):
        self.assertEqual(self.device.split_port("ADSL 0/2/4"), ("adsl", ("0", "2", "4")))
        self.assertEqual(self.device.split_port("GPON 0/6/7/1"), ("gpon", ("0", "6", "7", "1")))
        self.assertEqual(self.device.split_port("ethernet0/8/1"), ("eth", ("0", "8", "1")))
        self.assertEqual(self.device.split_port("ethernet0/9/2"), ("scu", ("0", "9", "2")))
        self.assertEqual(self.device.split_port("ethernet0/10/2"), ("giu", ("0", "10", "2")))
        self.assertEqual(self.device.split_port("/10/2"), ("", ("", "10", "2")))
        self.assertEqual(self.device.split_port("ge1/0/1"), ("", ("1", "0", "1")))
        self.assertEqual(self.device.split_port("2"), ("", ("2",)))

    def test_get_port_config(self):
        self.assertEqual(self.device.get_port_config("GPON 0/1/1/1"), "config\nline1\nline2\nline3")
        self.assertEqual(self.device.get_port_config("ethernet0/9/2"), "")

    def test_gpon_get_port_info(self):
        res = self.device.get_port_info("GPON 0/1/1")
        self.assertDictEqual(
            res,
            {
                "type": "gpon",
                "data": {
                    "total_count": "5",
                    "online_count": "4",
                    "onts_lines": [
                        [
                            "0",
                            "online",
                            "2023-07-15 04:11:34",
                            "2023-07-15 03:50:13",
                            "dying-gasp",
                            "2171",
                            "-22.84/2.01",
                        ],
                        ["1", "offline", "- ", "- ", "-", "-", "-/-"],
                        [
                            "2",
                            "online",
                            "2023-09-03 19:12:20",
                            "2023-08-29 01:15:16",
                            "dying-gasp",
                            "2166",
                            "-21.61/2.14",
                        ],
                        [
                            "3",
                            "online",
                            "2023-09-08 20:34:45",
                            "2023-09-02 20:35:31",
                            "dying-gasp",
                            "2155",
                            "-20.75/2.06",
                        ],
                        [
                            "4",
                            "online",
                            "2023-07-15 04:11:58",
                            "2023-07-15 03:50:13",
                            "dying-gasp",
                            "2170",
                            "-22.52/2.42",
                        ],
                    ],
                },
            },
        )

    def test_vdsl_get_port_info(self):
        res = self.device.get_port_info("VDSL 0/17/17")
        self.assertDictEqual(
            res,
            {
                "type": "adsl",
                "data": {
                    "profile_name": "VDSL LINE TEMPLATE 2",
                    "first_col": [],
                    "streams": [
                        {
                            "name": "Фактическая скорость передачи данных (Кбит/с)",
                            "down": {"value": "25580", "color": ""},
                            "up": {"value": "1396", "color": ""},
                        },
                        {
                            "name": "Максимальная скорость передачи данных (Кбит/с)",
                            "down": {"value": "25520", "color": ""},
                            "up": {"value": "1319", "color": ""},
                        },
                        {
                            "name": "Сигнал/Шум (дБ)",
                            "down": {"value": "7.2", "color": "#dde522"},
                            "up": {"value": "7.7", "color": "#dde522"},
                        },
                        {
                            "name": "Затухание линии (дБ)",
                            "down": {"value": "6.5", "color": "#22e536"},
                            "up": {"value": "10.4", "color": "#22e536"},
                        },
                        {
                            "name": "Общая выходная мощность (dBm)",
                            "down": {"value": "17.3", "color": "#95e522"},
                            "up": {"value": "9.8", "color": "#e5a522"},
                        },
                    ],
                    "profiles": [
                        ("5", "VDSL"),
                        ("4", "NO_CHANGE"),
                        ("3", "VDSL LINE TEMPLATE 3"),
                        ("2", "VDSL LINE TEMPLATE 2"),
                        ("1", "DEFVAL"),
                    ],
                },
            },
        )

    def test_adsl_get_port_info(self):
        res = self.device.get_port_info("ADSL 0/1/4")
        self.assertDictEqual(
            res,
            {
                "type": "adsl",
                "data": {
                    "profile_name": "N320-2464/2464-12896AnnexM",
                    "port": "ADSL 0/1/4",
                    "first_col": [
                        "Channel mode                              : Interleaved",
                        "Downstream channel bit swap               : Enable",
                        "Upstream channel bit swap                 : Enable",
                        "Trellis mode                              : Enable",
                        "Standard in port training                 : G992.5-Annex A",
                        "Current power management state            : Full-on state",
                    ],
                    "streams": [
                        {
                            "name": "Фактическая скорость передачи данных (Кбит/с)",
                            "down": {"color": "", "value": "12887"},
                            "up": {"color": "", "value": "1052"},
                        },
                        {
                            "name": "Максимальная скорость передачи данных (Кбит/с)",
                            "down": {"color": "", "value": "15666"},
                            "up": {"color": "", "value": "1247"},
                        },
                        {
                            "name": "Сигнал/Шум (дБ)",
                            "down": {"color": "#95e522", "value": "14.8"},
                            "up": {"color": "#95e522", "value": "10.2"},
                        },
                        {
                            "name": "Interleaved channel delay (ms)",
                            "down": {"color": "", "value": "5"},
                            "up": {"color": "", "value": "7"},
                        },
                        {
                            "name": "Затухание линии (дБ)",
                            "down": {"color": "#22e536", "value": "16.5"},
                            "up": {"color": "#22e536", "value": "8.6"},
                        },
                        {
                            "name": "Общая выходная мощность (dBm)",
                            "down": {"color": "#e5a522", "value": "2.0"},
                            "up": {"color": "#e5a522", "value": "6.3"},
                        },
                    ],
                    "profiles": [
                        ["31", "N160-1856/608-6432An nexM"],
                        ["32", "N320-2464/2464-12896 AnnexM"],
                        ["33", "N608-3008/4896-18720 AnnexM"],
                        ["1000", "ADSL LINEPROFILE 10 00"],
                    ],
                },
            },
        )

    def test_get_mac(self):
        res = self.device.get_mac("adsl 0/1/1")
        self.assertEqual(
            res,
            [
                (1418, "9afc-8d4c-1525"),
                (1418, "e0cc-f85d-3818"),
                (704, "bc76-706c-c671"),
                (735, "0002-cf93-db80"),
                (707, "0a31-92f7-1625"),
            ],
        )

    def test_invalid_get_port_info(self):
        invalid_res = {
            "type": "error",
            "data": "Неверный порт! (2)",
        }
        self.assertEqual(self.device.get_port_info("2"), invalid_res)
        invalid_res = {
            "type": "error",
            "data": "Неверный порт! (GPON 1/2)",
        }
        self.assertEqual(self.device.get_port_info("GPON 1/2"), invalid_res)
