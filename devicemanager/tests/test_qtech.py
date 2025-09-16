from devicemanager.vendors.qtech import Qtech

from .base_factory_test import AbstractTestFactory


class TestQTechFactory(AbstractTestFactory):
    @staticmethod
    def get_device_class():
        return Qtech

    @staticmethod
    def get_output_from_show_version_command() -> str:
        return """  QSW-8200-28F-AC-DC Device, Compiled on May 17 09:26:50 2016
  sysLocation Russia, Moscow, Novozavodskaya st 18, bld 1
  CPU Mac 00:1f:ce:33:22:11
  Vlan MAC 00:1f:ce:33:22:12
  SoftWare Package Version 7.0.3.5(R0224.0044)
  BootRom Version 7.1.103
  HardWare Version 2.0.3
  CPLD Version N/A
  Serial No.:1412000808
  Copyright (C) 2016 by QTECH LLC
  All rights reserved
  Last reboot is cold reset.
  Uptime is 38 weeks, 4 days, 22 hours, 49 minutes"""
