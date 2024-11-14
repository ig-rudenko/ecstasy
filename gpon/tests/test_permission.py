from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.urls import reverse
from rest_framework.test import APITestCase

User = get_user_model()


class TestTechDataListCreateAPIView(APITestCase):
    url = reverse("gpon-api:tech-data")
    view_permission_codenames = [
        "view_oltstate",
        "view_houseoltstate",
        "view_houseb",
        "view_end3",
    ]
    create_permission_codenames = [
        "add_oltstate",
        "add_houseoltstate",
        "add_houseb",
        "add_end3",
    ]

    def setUp(self) -> None:
        self.superuser = User.objects.create_superuser(
            username=f"{self.__class__.__name__}-superuser", password="password"
        )
        self.user = User.objects.create_user(username=f"{self.__class__.__name__}-user", password="password")
        self.view_group = Group.objects.create(name=f"view-{self.__class__.__name__}")
        perms = Permission.objects.filter(codename__in=self.view_permission_codenames)
        self.view_group.permissions.set(perms)

        self.create_group = Group.objects.create(name=f"create-{self.__class__.__name__}")
        perms = Permission.objects.filter(codename__in=self.create_permission_codenames)
        self.create_group.permissions.set(perms)

    # View

    def test_api_view_access_by_anonymous(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 401)

    def test_api_view_access_by_user_without_permissions(self):
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_api_view_access_by_superuser(self):
        self.client.force_login(self.superuser)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_api_view_access_by_user_with_view_permissions(self):
        self.user.groups.add(self.view_group)

        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    # Create

    def test_api_create_access_by_anonymous(self):
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 401)

    def test_api_create_access_by_user_without_permissions(self):
        self.client.force_login(self.user)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_api_create_access_by_superuser(self):
        self.client.force_login(self.superuser)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 400)

    def test_api_create_access_by_user_with_view_permissions(self):
        self.user.groups.add(self.view_group)

        self.client.force_login(self.user)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_api_create_access_by_user_with_create_permissions(self):
        self.user.groups.add(self.create_group)

        self.client.force_login(self.user)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 400)


class TestViewBuildingTechDataAPIView(APITestCase):
    url = reverse("gpon-api:view-building-tech-data", args=(1,))
    view_permission_codenames = [
        "view_oltstate",
        "view_houseoltstate",
        "view_houseb",
        "view_end3",
    ]

    def setUp(self) -> None:
        self.superuser = User.objects.create_superuser(
            username=f"{self.__class__.__name__}-superuser", password="password"
        )
        self.user = User.objects.create_user(username=f"{self.__class__.__name__}-user", password="password")
        self.view_group = Group.objects.create(name=f"view-{self.__class__.__name__}")
        perms = Permission.objects.filter(codename__in=self.view_permission_codenames)
        self.view_group.permissions.set(perms)

    # View

    def test_api_view_access_by_anonymous(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 401)

    def test_api_view_access_by_user_without_permissions(self):
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_api_view_access_by_superuser(self):
        self.client.force_login(self.superuser)
        resp = self.client.get(self.url)
        self.assertNotEqual(resp.status_code, 403)

    def test_api_view_access_by_user_with_view_permissions(self):
        self.user.groups.add(self.view_group)

        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertNotEqual(resp.status_code, 403)


class TestViewOLTStateTechDataAPIView(TestViewBuildingTechDataAPIView):
    url = reverse("gpon-api:tech-data-olt-state", args=(1,))


class TestViewUpdateEnd3TechCapabilityAPIView(APITestCase):
    url = reverse("gpon-api:tech-data-end3-capability", args=(1,))
    view_permission_codename = "view_end3"
    update_permission_codename = "change_end3"

    def setUp(self) -> None:
        self.superuser = User.objects.create_superuser(
            username=f"{self.__class__.__name__}-superuser", password="password"
        )
        self.user = User.objects.create_user(username=f"{self.__class__.__name__}-user", password="password")
        self.view_group = Group.objects.create(name=f"view-{self.__class__.__name__}")
        perms = Permission.objects.get(codename=self.view_permission_codename)
        self.view_group.permissions.add(perms)

        self.update_group = Group.objects.create(name=f"update-{self.__class__.__name__}")
        perms = Permission.objects.get(codename=self.update_permission_codename)
        self.update_group.permissions.add(perms)

    # View

    def test_api_view_access_by_anonymous(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 401)

    def test_api_view_access_by_user_without_permissions(self):
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_api_view_access_by_superuser(self):
        self.client.force_login(self.superuser)
        resp = self.client.get(self.url)
        self.assertNotEqual(resp.status_code, 403)  # NOT

    def test_api_view_access_by_user_with_view_permissions(self):
        self.user.groups.add(self.view_group)

        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertNotEqual(resp.status_code, 403)  # NOT

    # Update

    def test_api_update_access_by_anonymous(self):
        resp = self.client.put(self.url)
        self.assertEqual(resp.status_code, 401)

    def test_api_update_access_by_user_without_permissions(self):
        self.client.force_login(self.user)
        resp = self.client.put(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_api_update_access_by_superuser(self):
        self.client.force_login(self.superuser)
        resp = self.client.put(self.url)
        self.assertNotEqual(resp.status_code, 403)  # NOT

    def test_api_update_access_by_user_with_view_permissions(self):
        self.user.groups.add(self.update_group)

        self.client.force_login(self.user)
        resp = self.client.put(self.url)
        self.assertNotEqual(resp.status_code, 403)  # NOT


class TestTechCapabilityAPIView(TestViewUpdateEnd3TechCapabilityAPIView):
    url = reverse("gpon-api:tech-data-tech-capability", args=(1,))
    view_permission_codename = "view_techcapability"
    update_permission_codename = "change_techcapability"


class TestRetrieveUpdateOLTStateAPIView(TestViewUpdateEnd3TechCapabilityAPIView):
    url = reverse("gpon-api:tech-data-olt-state", args=(1,))
    view_permission_codename = "view_oltstate"
    update_permission_codename = "change_oltstate"


class TestRetrieveUpdateHouseOLTState(TestViewUpdateEnd3TechCapabilityAPIView):
    url = reverse("gpon-api:tech-data-house-olt-state", args=(1,))
    view_permission_codename = "view_houseoltstate"
    update_permission_codename = "change_houseoltstate"


# ============== SUBSCRIBER DATA ===============


class TestSubscriberConnectionListCreateAPIView(TestTechDataListCreateAPIView):
    url = reverse("gpon-api:subscribers-data-list-create")
    view_permission_codenames = [
        "view_customer",
        "view_subscriberconnection",
    ]
    create_permission_codenames = [
        "add_customer",
        "add_subscriberconnection",
    ]


class TestRetrieveUpdateCustomerDetailAPIView(TestViewUpdateEnd3TechCapabilityAPIView):
    url = reverse("gpon-api:customer-detail", args=(1,))
    view_permission_codename = "view_customer"
    update_permission_codename = "change_customer"


class TestViewListAPIView(TestViewBuildingTechDataAPIView):
    url = reverse("gpon-api:customers-list")
    view_permission_codenames = ["view_customer"]
