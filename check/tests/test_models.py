from django.test import TestCase
from check.models import Devices, DeviceGroup, AuthGroup, Bras, Profile, UsersActions
from django.contrib.auth.models import User


class DeviceModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Devices.objects.create(name="Test Name", ip="192.168.123.123")

    # NAME
    def test_device_name_label(self):
        dev = Devices.objects.all().first()
        name_label = dev._meta.get_field("name").verbose_name
        self.assertEqual(name_label, "Имя оборудования")

    def test_device_name_max_length(self):
        dev = Devices.objects.all().first()
        max_length = dev._meta.get_field("name").max_length
        self.assertEqual(max_length, 100)

    # IP
    def test_ip_label(self):
        dev = Devices.objects.all().first()
        ip_label = dev._meta.get_field("ip").verbose_name
        self.assertEqual(ip_label, "IP адрес")

    def test_ip_max_length(self):
        dev = Devices.objects.all().first()
        max_length = dev._meta.get_field("ip").max_length
        self.assertEqual(max_length, 39)

    # VENDOR
    def test_vendor_label(self):
        dev = Devices.objects.all().first()
        vendor_label = dev._meta.get_field("vendor").verbose_name
        self.assertEqual(vendor_label, "Производитель")

    def test_vendor_max_length(self):
        dev = Devices.objects.all().first()
        max_length = dev._meta.get_field("vendor").max_length
        self.assertEqual(max_length, 100)

    # SNMP_COMMUNITY
    def test_snmp_comm_label(self):
        dev = Devices.objects.all().first()
        label = dev._meta.get_field("snmp_community").verbose_name
        self.assertEqual(label, "SNMP community")

    def test_snmp_comm_max_length(self):
        dev = Devices.objects.all().first()
        max_length = dev._meta.get_field("snmp_community").max_length
        self.assertEqual(max_length, 64)

    def test_default_snmp_comm(self):
        dev = Devices.objects.all().first()
        self.assertEqual(dev.snmp_community, None)

    # port_scan_protocol
    def test_port_scan_protocol_label(self):
        dev = Devices.objects.all().first()
        label = dev._meta.get_field("port_scan_protocol").verbose_name
        self.assertEqual(label, "Протокол для поиска интерфейсов")

    def test_port_scan_protocol_max_length(self):
        dev = Devices.objects.all().first()
        max_length = dev._meta.get_field("port_scan_protocol").max_length
        self.assertEqual(max_length, 6)

    def test_default_port_scan_protocol(self):
        dev = Devices.objects.all().first()
        self.assertEqual(dev.port_scan_protocol, "telnet")

    # cmd_protocol
    def test_cmd_protocol_label(self):
        dev = Devices.objects.all().first()
        label = dev._meta.get_field("cmd_protocol").verbose_name
        self.assertEqual(label, "Протокол для выполнения команд")

    def test_cmd_protocol_max_length(self):
        dev = Devices.objects.all().first()
        max_length = dev._meta.get_field("cmd_protocol").max_length
        self.assertEqual(max_length, 6)

    def test_default_cmd_protocol(self):
        dev = Devices.objects.all().first()
        self.assertEqual(dev.port_scan_protocol, "telnet")

    # STR
    def test_object_to_str(self):
        dev = Devices.objects.all().first()
        self.assertEqual(f"{dev.name} ({dev.ip})", str(dev))

    def test_absolute_url(self):
        dev = Devices.objects.all().first()
        self.assertEqual(dev.get_absolute_url(), "/device/" + dev.name)


class DeviceGroupTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        DeviceGroup.objects.create(name="Test Group", description="Description")

    # NAME
    def test_name_label(self):
        g = DeviceGroup.objects.all().first()
        label = g._meta.get_field("name").verbose_name
        self.assertEqual(label, "Название")

    def test_name_max_length(self):
        g = DeviceGroup.objects.all().first()
        max_length = g._meta.get_field("name").max_length
        self.assertEqual(max_length, 100)

    # DESCRIPTION
    def test_description_label(self):
        g = DeviceGroup.objects.all().first()
        label = g._meta.get_field("description").verbose_name
        self.assertEqual(label, "Описание")

    def test_description_max_length(self):
        g = DeviceGroup.objects.all().first()
        max_length = g._meta.get_field("description").max_length
        self.assertEqual(max_length, 255)

    # STR
    def test_object_to_str(self):
        g = DeviceGroup.objects.all().first()
        self.assertEqual(f"[ {g.name} ]", str(g))


class AuthGroupTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        AuthGroup.objects.create(
            name="Test Auth",
            login="login",
            password="password",
            secret="secret",
            description="Description",
        )

    # NAME
    def test_name_label(self):
        g = AuthGroup.objects.all().first()
        label = g._meta.get_field("name").verbose_name
        self.assertEqual(label, "Название")

    def test_name_max_length(self):
        g = AuthGroup.objects.all().first()
        max_length = g._meta.get_field("name").max_length
        self.assertEqual(max_length, 100)

    # LOGIN
    def test_login_label(self):
        g = AuthGroup.objects.all().first()
        label = g._meta.get_field("login").verbose_name
        self.assertEqual(label, "Логин")

    def test_login_max_length(self):
        g = AuthGroup.objects.all().first()
        max_length = g._meta.get_field("login").max_length
        self.assertEqual(max_length, 64)

    # PASSWORD
    def test_password_label(self):
        g = AuthGroup.objects.all().first()
        label = g._meta.get_field("password").verbose_name
        self.assertEqual(label, "Пароль")

    def test_password_max_length(self):
        g = AuthGroup.objects.all().first()
        max_length = g._meta.get_field("password").max_length
        self.assertEqual(max_length, 64)

    # PASSWORD
    def test_secret_label(self):
        g = AuthGroup.objects.all().first()
        label = g._meta.get_field("secret").verbose_name
        self.assertEqual(label, "Пароль от привилегированного режима")

    def test_secret_max_length(self):
        g = AuthGroup.objects.all().first()
        max_length = g._meta.get_field("secret").max_length
        self.assertEqual(max_length, 64)

    # DESCRIPTION
    def test_description_label(self):
        g = AuthGroup.objects.all().first()
        label = g._meta.get_field("description").verbose_name
        self.assertEqual(label, "Описание")

    def test_description_max_length(self):
        g = AuthGroup.objects.all().first()
        max_length = g._meta.get_field("description").max_length
        self.assertEqual(max_length, 255)

    # STR
    def test_object_to_str(self):
        g = AuthGroup.objects.all().first()
        self.assertEqual(f"< {g.name} >", str(g))


class DeviceRelationsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        group = DeviceGroup.objects.create(name="Test Group", description="Description")
        auth = AuthGroup.objects.create(
            name="Test Auth",
            login="login",
            password="password",
            secret="secret",
            description="Description",
        )
        Devices.objects.create(name="Test Name", ip="192.168.123.123", group=group, auth_group=auth)

    def test_relation(self):
        dev = Devices.objects.get(ip="192.168.123.123")
        self.assertEqual(dev.auth_group.name, "Test Auth")
        self.assertEqual(dev.auth_group.login, "login")
        self.assertEqual(dev.auth_group.password, "password")
        self.assertEqual(dev.group.name, "Test Group")


class BrasTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.bras = Bras.objects.create(name="BRAS", ip="192.168.1.1", login="login", password="password")

    # NAME
    def test_name_label(self):
        label = self.bras._meta.get_field("name").verbose_name
        self.assertEqual(label, "Название")

    def test_name_max_length(self):
        max_length = self.bras._meta.get_field("name").max_length
        self.assertEqual(max_length, 10)

    # IP
    def test_ip_label(self):
        label = self.bras._meta.get_field("ip").verbose_name
        self.assertEqual(label, "IP адрес")

    def test_ip_max_length(self):
        max_length = self.bras._meta.get_field("ip").max_length
        self.assertEqual(max_length, 39)

    # LOGIN
    def test_login_label(self):
        label = self.bras._meta.get_field("login").verbose_name
        self.assertEqual(label, "Логин")

    def test_login_max_length(self):
        max_length = self.bras._meta.get_field("login").max_length
        self.assertEqual(max_length, 64)

    # LOGIN
    def test_password_label(self):
        label = self.bras._meta.get_field("password").verbose_name
        self.assertEqual(label, "Пароль")

    def test_password_max_length(self):
        max_length = self.bras._meta.get_field("password").max_length
        self.assertEqual(max_length, 64)

    # SECRET
    def test_secret_label(self):
        label = self.bras._meta.get_field("secret").verbose_name
        self.assertEqual(label, "Пароль от привилегированного режима")

    def test_secret_max_length(self):
        max_length = self.bras._meta.get_field("secret").max_length
        self.assertEqual(max_length, 64)

    # STR
    def test_str(self):
        self.assertEqual(self.bras.name, str(self.bras))


class ProfileTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        u = User(first_name="First_Name", email="email@email.com", username="first_user")
        u.set_password("user_password")
        u.save()

    def test_auto_create_profile(self):
        p = Profile.objects.get(user__username="first_user")
        self.assertEqual(p.user.username, "first_user")

    def test_default_permissions(self):
        p = Profile.objects.get(user=User.objects.get(username="first_user"))
        self.assertEqual(p.permissions, "read")

    def test_permissions_list(self):
        p = Profile.objects.get(user=User.objects.get(username="first_user"))
        self.assertEqual(p.permissions_level, ["read", "reboot", "up_down", "bras"])

    def test_permissions_max_length(self):
        p = Profile.objects.get(user=User.objects.get(username="first_user"))
        max_length = p._meta.get_field("permissions").max_length
        self.assertEqual(max_length, 15)

    def test_str(self):
        p = Profile.objects.get(user=User.objects.get(username="first_user"))
        self.assertEqual(str(p), f"Profile: {p.user.username}")


class UsersActionsTest(TestCase):
    def setUp(self) -> None:
        u1 = User(username="test_user1")
        u1.set_password("password")
        u1.save()
        u2 = User(username="test_user2")
        u2.set_password("password")
        u2.save()

        dev = Devices.objects.create(name="Device1", ip="10.101.10.101")

        # По 50 действий для 2х пользователей
        for i in range(1, 101):
            UsersActions.objects.create(
                device=dev,
                user=u1 if i % 2 == 0 else u2,
                action=f"Действия пользователя-{i}",
            )

    def tearDown(self) -> None:
        User.objects.all().delete()
        UsersActions.objects.all().delete()
        Devices.objects.all().delete()

    def test_user_action(self):
        u1 = User.objects.get(username="test_user1")
        actions = UsersActions.objects.filter(user=u1)

        self.assertEqual(len(actions), 50)

    def test_user_action_when_delete_one_user(self):
        # После удаления пользователя, удаляются его логи
        u1 = User.objects.get(username="test_user1").delete()
        actions = UsersActions.objects.filter(user=u1)
        self.assertEqual(len(actions), 0)

        # Для другого пользователя все остается
        u2 = User.objects.get(username="test_user2")
        actions = UsersActions.objects.filter(user=u2)
        self.assertEqual(len(actions), 50)

    def test_user_action_when_delete_devices(self):
        # После удаления всех устройств, удаляются и логи
        Devices.objects.all().delete()
        actions = UsersActions.objects.all()
        self.assertEqual(len(actions), 0)
