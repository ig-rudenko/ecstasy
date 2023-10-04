from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from gpon.models import HouseB


@login_required
def gpon_home(request):
    return render(request, "gpon/main.html")


@login_required
def gpon_tech_data(request):
    return render(request, "gpon/tech-data.html")


@login_required
def gpon_create_tech_data(request):
    return render(request, "gpon/create-tech-data.html")


@login_required
def gpon_view_olt_tech_data(request, device_name: str):
    return render(
        request,
        "gpon/view-olt-tech-data.html",
        {"device_name": device_name, "disable_container": True},
    )


@login_required
def gpon_view_building_tech_data(request, building_id: int):
    house = get_object_or_404(HouseB, id=building_id)
    return render(
        request,
        "gpon/view-building-tech-data.html",
        {"address": house.address.verbose, "disable_container": True},
    )
