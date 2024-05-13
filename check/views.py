"""
# Функции представления для взаимодействия с оборудованием
"""
from django.contrib.auth.decorators import login_required
from django.db.models import QuerySet
from django.http import (
    HttpResponseRedirect,
    Http404,
    HttpRequest,
)
from django.shortcuts import render, resolve_url

from devicemanager.device import DeviceManager
from . import models


def by_zabbix_host_id(request: HttpRequest, host_id: str):
    """
    ## Преобразование идентификатора узла сети "host_id" Zabbix в URL ecstasy.

    :param request: Запрос.
    :param host_id: Идентификатор узла сети в Zabbix.
    """

    dev = DeviceManager.from_hostid(host_id)
    if dev is None:
        raise Http404

    # Ищем по имени
    found_dev: QuerySet[models.Devices] = models.Devices.objects.filter(name=dev.name)
    if not found_dev.exists():
        # Или по IP
        found_dev = models.Devices.objects.filter(ip=dev.ip)

    model_dev = found_dev.first()
    if not model_dev:
        # Не нашли оборудование
        raise Http404

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
