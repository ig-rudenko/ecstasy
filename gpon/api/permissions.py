from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request
from rest_framework.views import APIView


class UserBasePermission(BasePermission):
    safe_permissions_list: list[str] = []
    create_permissions_list: list[str] = []
    update_permissions_list: list[str] = []
    delete_permissions_list: list[str] = []

    def __init__(self):
        super().__init__()
        self.method = "GET"

    @property
    def message(self) -> str:
        if self.method in SAFE_METHODS:
            return "У вас нет доступа для просмотра данной информации"
        elif self.method == "POST":
            return "У вас нет доступа для создания"
        elif self.method in ["PUT", "PATCH"]:
            return "У вас нет доступа для изменения данного элемента"
        elif self.method == "DELETE":
            return "У вас нет доступа для удаления данной записи"
        return "Данный метод не разрешен"

    def has_permission(self, request: Request, view: APIView) -> bool:
        self.method = request.method
        if request.method in SAFE_METHODS:
            return bool(
                self.safe_permissions_list
                and request.user.has_perms(
                    self.safe_permissions_list,
                )
            )
        elif request.method == "POST":
            return bool(self.create_permissions_list and request.user.has_perms(self.create_permissions_list))
        elif request.method in ["PUT", "PATCH"]:
            return bool(self.update_permissions_list and request.user.has_perms(self.update_permissions_list))
        elif request.method == "DELETE":
            return bool(self.delete_permissions_list and request.user.has_perms(self.delete_permissions_list))
        return False


class TechDataPermission(UserBasePermission):
    safe_permissions_list = [
        "gpon.view_oltstate",
        "gpon.view_houseoltstate",
        "gpon.view_houseb",
    ]
    create_permissions_list = [
        "gpon.add_oltstate",
        "gpon.add_houseoltstate",
        "gpon.add_houseb",
    ]
    update_permissions_list = [
        "gpon.change_oltstate",
        "gpon.change_houseoltstate",
        "gpon.change_houseb",
    ]
    delete_permissions_list = [
        "gpon.delete_oltstate",
        "gpon.delete_houseoltstate",
        "gpon.delete_houseb",
    ]


class SubscriberDataPermission(UserBasePermission):
    safe_permissions_list = [
        "gpon.view_customer",
        "gpon.view_subscriberconnection",
    ]
    create_permissions_list = [
        "gpon.add_customer",
        "gpon.add_subscriberconnection",
    ]
    update_permissions_list = [
        "gpon.change_customer",
        "gpon.change_subscriberconnection",
    ]
    delete_permissions_list = [
        "gpon.delete_customer",
        "gpon.delete_subscriberconnection",
    ]


class OLTStatePermission(UserBasePermission):
    safe_permissions_list = ["gpon.view_oltstate"]
    create_permissions_list = ["gpon.add_oltstate"]
    update_permissions_list = ["gpon.change_oltstate"]
    delete_permissions_list = ["gpon.delete_oltstate"]


class HouseOLTStatePermission(UserBasePermission):
    safe_permissions_list = ["gpon.view_houseoltstate"]
    create_permissions_list = ["gpon.add_houseoltstate"]
    update_permissions_list = ["gpon.change_houseoltstate"]
    delete_permissions_list = ["gpon.delete_houseoltstate"]


class HouseBPermission(UserBasePermission):
    safe_permissions_list = ["gpon.view_houseb"]
    create_permissions_list = ["gpon.add_houseb"]
    update_permissions_list = ["gpon.change_houseb"]
    delete_permissions_list = ["gpon.delete_houseb"]


class End3Permission(UserBasePermission):
    safe_permissions_list = ["gpon.view_end3"]
    create_permissions_list = ["gpon.add_end3"]
    update_permissions_list = ["gpon.change_end3"]
    delete_permissions_list = ["gpon.delete_end3"]


class TechCapabilityPermission(UserBasePermission):
    safe_permissions_list = ["gpon.view_techcapability"]
    create_permissions_list = ["gpon.add_techcapability"]
    update_permissions_list = ["gpon.change_techcapability"]
    delete_permissions_list = ["gpon.delete_techcapability"]


class CustomerPermission(UserBasePermission):
    safe_permissions_list = ["gpon.view_customer"]
    create_permissions_list = ["gpon.add_customer"]
    update_permissions_list = ["gpon.change_customer"]
    delete_permissions_list = ["gpon.delete_customer"]
