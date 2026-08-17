from typing import ClassVar

from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from apps.accounting.models import User

from ..models import Profile


class InterfaceChangeDescriptionAdminTest(TestCase):
    """Проверка нового права в стандартных формах и списках админки."""

    admin_user: ClassVar[User]
    managed_user: ClassVar[User]
    permission: ClassVar[Permission]
    group: ClassVar[Group]

    @classmethod
    def setUpTestData(cls) -> None:
        """Создать администратора и объекты с новым правом."""
        cls.admin_user = User.objects.create_superuser(username="admin", password="password")
        cls.managed_user = User.objects.create_user(username="managed-user", password="password")
        cls.permission = Profile.get_permission(Profile.INTERFACE_CHANGE_DESC).get()
        cls.managed_user.user_permissions.add(cls.permission)
        cls.group = Group.objects.create(name="Interface description operators")
        cls.group.permissions.add(cls.permission)

    def setUp(self) -> None:
        """Авторизовать администратора перед каждым запросом."""
        self.client.force_login(self.admin_user)

    def test_user_admin_form_contains_permission(self):
        """Форма пользователя должна отображать новое право."""
        response = self.client.get(reverse("admin:accounting_user_change", args=(self.managed_user.pk,)))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Изменение описания порта")

    def test_group_admin_form_contains_permission(self):
        """Форма группы должна отображать новое право."""
        response = self.client.get(reverse("admin:auth_group_change", args=(self.group.pk,)))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Изменение описания порта")

    def test_profile_admin_list_displays_permission(self):
        """Список профилей должен отображать codename нового права."""
        response = self.client.get(reverse("admin:check_profile_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "interface_change_desc")
