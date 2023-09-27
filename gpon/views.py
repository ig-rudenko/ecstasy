from django.contrib.auth.decorators import login_required
from django.shortcuts import render


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
    return render(request, "gpon/view-olt-tech-data.html", {"device_name": device_name})
