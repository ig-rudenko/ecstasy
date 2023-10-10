from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request
from rest_framework.views import APIView


class UserBasePermission(BasePermission):
    message = "У вас нет доступа для просмотра данной информации"
    safe_permissions_list = []
    create_permissions_list = []
    update_permissions_list = []
    delete_permissions_list = []

    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method in SAFE_METHODS:
            return self.safe_permissions_list and request.user.has_perms(
                self.safe_permissions_list,
            )
        elif request.method == "POST":
            return self.create_permissions_list and request.user.has_perms(
                self.create_permissions_list
            )
        elif request.method in ["PUT", "PATCH"]:
            return self.update_permissions_list and request.user.has_perms(
                self.update_permissions_list
            )
        elif request.method == "DELETE":
            return self.delete_permissions_list and request.user.has_perms(
                self.delete_permissions_list
            )


class TechDataPermission(UserBasePermission):
    message = "У вас нет доступа для просмотра данной информации"
    safe_permissions_list = [
        "gpon.view_oltstate",
        "gpon.view_houseoltstate",
        "gpon.view_houseb",
        "gpon.view_end3",
    ]
    create_permissions_list = [
        "gpon.add_oltstate",
        "gpon.add_houseoltstate",
        "gpon.add_houseb",
        "gpon.add_end3",
    ]
