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
