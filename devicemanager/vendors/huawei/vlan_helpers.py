import re

from devicemanager.vendors.base.types import VlanTableType


def parse_vlan_table_quidway_s2403(output: str) -> VlanTableType:
    """
    Парсит вывод:
         VLAN ID: 1
         VLAN Type: static
         Route Interface: not configured
         Description: VLAN 0001
         Name: VLAN 0001
         Tagged   Ports: none
         Untagged Ports: none

         VLAN ID: 501
         VLAN Type: static
         Route Interface: configured
         IP Address: 192.168.102.200
         Subnet Mask: 255.255.255.0
         Description: VLAN 0501
         Name: managment
         Tagged   Ports:
          GigabitEthernet1/1/1     GigabitEthernet1/2/2
         Untagged Ports: none

         VLAN ID: 605
         VLAN Type: static
         Service Type: multicast vlan
         Route Interface: not configured
         Description: local_dhcp
         Name: VLAN 0605
         Tagged   Ports:
          GigabitEthernet1/1/1     GigabitEthernet1/2/2
         Untagged Ports: none

         VLAN ID: 716
         VLAN Type: static
         Route Interface: not configured
         Description: VLAN 0716
         Name: INET_Bill_716
         Tagged   Ports:
          GigabitEthernet1/1/1     GigabitEthernet1/2/2
         Untagged Ports:
          Ethernet1/0/1            Ethernet1/0/2            Ethernet1/0/3
          Ethernet1/0/4            Ethernet1/0/5            Ethernet1/0/6
          Ethernet1/0/7            Ethernet1/0/8            Ethernet1/0/9
          Ethernet1/0/10           Ethernet1/0/11           Ethernet1/0/12
          Ethernet1/0/13           Ethernet1/0/14           Ethernet1/0/15
          Ethernet1/0/16           Ethernet1/0/17           Ethernet1/0/18
          Ethernet1/0/19           Ethernet1/0/20           Ethernet1/0/21
          Ethernet1/0/22           Ethernet1/0/23           Ethernet1/0/24
    """
    regexp = re.compile(
        r"VLAN ID: (?P<vid>\d+).+?Name: (?P<name>.+?\n).+?Tagged\s+Ports:\s+(?P<tagged_ports>.+?)Untagged\s+Ports:\s+(?P<untagged_ports>.+?)(?=VLAN|$)",
        flags=re.DOTALL,
    )

    result: VlanTableType = []

    for line in regexp.finditer(output):
        vlan_name = line.group("name").strip()
        tagged_ports = re.split(r"\s+", line.group("tagged_ports").strip())
        untagged_ports = re.split(r"\s+", line.group("untagged_ports").strip())
        ports = list(filter(lambda x: x != "none", [*tagged_ports, *untagged_ports]))

        result.append((int(line.group("vid")), ports, vlan_name))

    return result


def parse_vlan_table_quidway_s2326(output: str) -> VlanTableType:
    """
    Парсит вывод:

        The total number of vlans is : 6
        --------------------------------------------------------------------------------
        U: Up;         D: Down;         TG: Tagged;         UT: Untagged;
        MP: Vlan-mapping;               ST: Vlan-stacking;
        #: ProtocolTransparent-vlan;    *: Management-vlan;
        --------------------------------------------------------------------------------

        VID  Type    Ports
        --------------------------------------------------------------------------------
        1    common  UT:GE0/0/1(U)      GE0/0/2(U)
        700  common  UT:Eth0/0/2(D)     Eth0/0/4(U)     Eth0/0/5(U)     Eth0/0/6(D)
                        Eth0/0/7(D)     Eth0/0/8(D)     Eth0/0/9(D)     Eth0/0/10(D)
                        Eth0/0/11(D)    Eth0/0/13(D)    Eth0/0/14(D)    Eth0/0/15(D)
                        Eth0/0/16(D)    Eth0/0/17(D)    Eth0/0/18(D)    Eth0/0/19(D)
                        Eth0/0/20(D)    Eth0/0/21(D)    Eth0/0/22(D)    Eth0/0/23(D)
                     TG:GE0/0/1(U)      GE0/0/2(U)
        800  *common TG:GE0/0/1(U)      GE0/0/2(U)
        801  common  TG:GE0/0/1(U)      GE0/0/2(U)
        811  common  UT:Eth0/0/24(D)
                     TG:GE0/0/1(U)      GE0/0/2(U)

        VID  Status  Property      MAC-LRN Statistics Description
        --------------------------------------------------------------------------------
        1    enable  default       enable  disable    VLAN 0001
        700  enable  multicastVLAN enable  disable    VLAN 0700
        800  enable  default       enable  disable    VLAN 0800
        801  enable  multicastVLAN enable  disable    VLAN 0801
        811  enable  default       enable  disable    VLAN 0811
    """

    regexp = re.compile(
        r"(?P<vid>\d+)\s+\S+\s+(?:TG|UT|MP|ST):(?P<ports>.+?)(?=(\d+\s+\S+\s+(?:TG|UT|MP|ST)|\s*\n\s*\n))",
        flags=re.DOTALL,
    )

    result: VlanTableType = []

    for line in regexp.finditer(output):
        vlan_name = ""
        vid = int(line.group("vid"))
        ports_line = re.sub(r"\(\S\)|TG:|UT:|MP:|ST:", "", line.group("ports").strip())
        ports = re.split(r"\s+", ports_line)

        if vlan_name_match := re.search(rf"{vid}\s+enable\s+\S+\s+\S+\s+\S+\s+(?P<name>.+?)\s*\n", output):
            vlan_name = vlan_name_match.group("name").strip()

        result.append((int(line.group("vid")), ports, vlan_name))

    return result
