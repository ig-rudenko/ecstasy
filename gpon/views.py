from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404

from gpon.api.permissions import TechDataPermission, End3Permission, SubscriberDataPermission
from gpon.models import HouseB, End3


@login_required
def gpon_home(request):
    return render(request, "gpon/main.html")


@login_required
@permission_required(TechDataPermission.safe_permissions_list, raise_exception=True)
def gpon_tech_data(request):
    return render(request, "gpon/tech-data.html")


@login_required
@permission_required(TechDataPermission.create_permissions_list, raise_exception=True)
def gpon_create_tech_data(request):
    return render(request, "gpon/create-tech-data.html")


@login_required
@permission_required(TechDataPermission.safe_permissions_list, raise_exception=True)
def gpon_view_olt_tech_data(request, device_name: str):
    return render(
        request,
        "gpon/view-olt-tech-data.html",
        {"device_name": device_name, "disable_container": True},
    )


@login_required
@permission_required(TechDataPermission.safe_permissions_list, raise_exception=True)
def gpon_view_building_tech_data(request, building_id: int):
    house = get_object_or_404(HouseB, id=building_id)
    return render(
        request,
        "gpon/view-building-tech-data.html",
        {"address": house.address.verbose, "disable_container": True},
    )


@login_required
@permission_required(End3Permission.create_permissions_list, raise_exception=True)
def gpon_view_end3_tech_data(request, pk: int):
    end3 = get_object_or_404(End3, pk=pk)
    return render(
        request, "gpon/view-end3-tech-data.html", {"end3": end3, "disable_container": True}
    )


@login_required
@permission_required(SubscriberDataPermission.safe_permissions_list, raise_exception=True)
def gpon_subscriber_data(request):
    return render(request, "gpon/subscriber-data.html")


@login_required
@permission_required(SubscriberDataPermission.create_permissions_list, raise_exception=True)
def gpon_create_subscriber_data(request):
    return render(request, "gpon/create-subscriber-data.html")
