from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class BrasDeviceMigrationTest(TransactionTestCase):
    """Проверка переноса настроек подключения BRAS в Devices."""

    migrate_from = ("check", "0041_deviceinterfacepatternrule")
    migrate_to = ("check", "0042_bras_device")

    def setUp(self) -> None:
        """Подготовить базу в состоянии до проверяемой миграции."""
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_from])
        self.old_apps = executor.loader.project_state([self.migrate_from]).apps

    def tearDown(self) -> None:
        """Вернуть базу к актуальному состоянию миграций."""
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_migration_reuses_existing_device_and_creates_missing_device(self):
        """Миграция должна связать BRAS с Devices без потери настроек."""
        AuthGroup = self.old_apps.get_model("check", "AuthGroup")
        Bras = self.old_apps.get_model("check", "Bras")
        DeviceGroup = self.old_apps.get_model("check", "DeviceGroup")
        Devices = self.old_apps.get_model("check", "Devices")

        group = DeviceGroup.objects.create(name="Network")
        existing_auth = AuthGroup.objects.create(
            name="Existing auth",
            login="existing",
            password="existing-password",
        )
        existing_device = Devices.objects.create(
            name="Existing BRAS",
            ip="192.0.2.1",
            group=group,
            auth_group=existing_auth,
        )
        Bras.objects.create(
            name="OLD",
            ip=existing_device.ip,
            login="legacy",
            password="legacy-password",
            connection_pool_size=3,
        )
        Bras.objects.create(
            name="NEW",
            ip="192.0.2.2",
            login="new-login",
            password="new-password",
            secret="new-secret",
            connection_pool_size=4,
        )

        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_to])
        apps = executor.loader.project_state([self.migrate_to]).apps
        MigratedBras = apps.get_model("check", "Bras")
        MigratedDevices = apps.get_model("check", "Devices")

        reused_bras = MigratedBras.objects.get(device__ip="192.0.2.1")
        self.assertEqual(reused_bras.device_id, existing_device.pk)
        self.assertEqual(reused_bras.device.auth_group.login, "existing")

        created_bras = MigratedBras.objects.get(device__ip="192.0.2.2")
        created_device = MigratedDevices.objects.get(pk=created_bras.device_id)
        self.assertEqual(created_device.name, "NEW")
        self.assertEqual(created_device.auth_group.login, "new-login")
        self.assertEqual(created_device.auth_group.password, "new-password")
        self.assertEqual(created_device.auth_group.secret, "new-secret")
        self.assertEqual(created_device.connection_pool_size, 4)


class InterfaceChangeDescriptionPermissionMigrationTest(TransactionTestCase):
    """Проверка сохранения доступа при выделении отдельного права интерфейсов."""

    migrate_from = ("check", "0043_profile_permissions_to_auth_permissions")
    migrate_to = ("check", "0044_add_interface_change_desc_permission")

    def setUp(self) -> None:
        """Подготовить пользователей и группы со старым BRAS-правом."""
        super().setUp()
        executor = MigrationExecutor(connection)
        migration_targets = [
            self.migrate_from,
            ("accounting", "0004_move_user_to_accounting_table"),
        ]
        executor.migrate(migration_targets)
        old_apps = executor.loader.project_state(migration_targets).apps

        ContentType = old_apps.get_model("contenttypes", "ContentType")
        Group = old_apps.get_model("auth", "Group")
        Permission = old_apps.get_model("auth", "Permission")
        User = old_apps.get_model("accounting", "User")

        content_type, _ = ContentType.objects.get_or_create(app_label="check", model="profile")
        legacy_permission, _ = Permission.objects.get_or_create(
            codename="device_bras_read_write",
            content_type=content_type,
            defaults={"name": "Сброс сессий BRAS"},
        )
        direct_user = User.objects.create(username="direct-bras-user")
        direct_user.user_permissions.add(legacy_permission)
        plain_user = User.objects.create(username="plain-user")
        bras_group = Group.objects.create(name="BRAS operators")
        bras_group.permissions.add(legacy_permission)
        plain_group = Group.objects.create(name="Plain operators")
        self.direct_user_id = direct_user.pk
        self.plain_user_id = plain_user.pk
        self.bras_group_id = bras_group.pk
        self.plain_group_id = plain_group.pk

    def tearDown(self) -> None:
        """Вернуть базу к актуальному состоянию миграций."""
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_migration_copies_legacy_permission_for_users_and_groups(self):
        """Новое право должно наследовать прямые и групповые назначения старого."""
        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_to])
        apps = executor.loader.project_state([self.migrate_to]).apps

        Group = apps.get_model("auth", "Group")
        Permission = apps.get_model("auth", "Permission")
        User = apps.get_model("accounting", "User")
        new_permission = Permission.objects.get(
            content_type__app_label="check",
            content_type__model="profile",
            codename="device_interface_change_desc",
        )
        direct_user = User.objects.get(pk=self.direct_user_id)
        plain_user = User.objects.get(pk=self.plain_user_id)
        bras_group = Group.objects.get(pk=self.bras_group_id)
        plain_group = Group.objects.get(pk=self.plain_group_id)

        self.assertTrue(direct_user.user_permissions.filter(pk=new_permission.pk).exists())
        self.assertFalse(plain_user.user_permissions.filter(pk=new_permission.pk).exists())
        self.assertTrue(bras_group.permissions.filter(pk=new_permission.pk).exists())
        self.assertFalse(plain_group.permissions.filter(pk=new_permission.pk).exists())
        self.assertTrue(direct_user.user_permissions.filter(codename="device_bras_read_write").exists())
        self.assertTrue(bras_group.permissions.filter(codename="device_bras_read_write").exists())
