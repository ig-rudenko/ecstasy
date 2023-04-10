"""
# Функции представления для взаимодействия с оборудованием
"""

from django.http import (
    HttpResponseRedirect,
    Http404,
)
from django.shortcuts import render, resolve_url
from django.contrib.auth.decorators import login_required

from devicemanager import Device
from . import models


def by_zabbix_hostid(request, hostid: str):
    """
    ## Преобразование идентификатора узла сети "host_id" Zabbix в URL ecstasy

    :param hostid: Идентификатор узла сети в Zabbix
    """

    dev = Device.from_hostid(hostid)
    if not dev:
        raise Http404

    # Ищем по имени
    found_dev = models.Devices.objects.filter(name=dev.name)
    if not found_dev.exists():
        # Или по IP
        found_dev = models.Devices.objects.filter(ip=dev.ip)

    if not found_dev.exists():
        # Не нашли оборудование
        raise Http404

    model_dev = found_dev.first()
    return HttpResponseRedirect(resolve_url("device_info", name=model_dev.name))


@login_required
def home(request):
    """
    ## Домашняя страница
    """

    return render(request, "home.html")


@login_required
def show_devices(request):
    """
    ## Список всех имеющихся устройств
    """

    return render(request, "check/devices.html")


@login_required
def device_info(request, name: str):
    """
    ## Вывод главной информации об устройстве и его интерфейсов
    """

    return render(request, "check/device_info.html", {"device_name": name})
