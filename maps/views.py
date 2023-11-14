from functools import wraps

from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseForbidden, Http404
from django.shortcuts import render, get_object_or_404

from .models import Maps


def access_to_map(function):
    """
    Декоратор проверяет, есть ли пользователь в списке пользователей карты,
    и если да, то вызывает исходную функцию, либо 403.
    """

    @wraps(function)
    def wrapper(request, map_id, *args, **kwargs):
        map_ = get_object_or_404(Maps, id=map_id)

        # Проверяет, есть ли пользователь в списке пользователей карты.
        if request.user.is_superuser or map_.users.contains(request.user):
            return function(request, map_, *args, **kwargs)

        # Возвращаем ответ с кодом состояния 403.
        return HttpResponseForbidden()

    return wrapper


@login_required
@permission_required("auth.can_view_maps", raise_exception=True)
def map_home(request):
    return render(
        request, "maps/home.html", {"maps": Maps.objects.filter(users=request.user)}
    )


@login_required
@access_to_map
def show_interactive_map(request, map_obj: Maps):
    """
    ## Возвращаем карту в зависимости от её типа.
    """

    # Проверяет тип карты. Если карта имеет тип "zabbix", то возвращает шаблон интерактивной карты.
    if map_obj.type == "zabbix":
        return render(request, "maps/interactive_map.html", {"map": map_obj})

    # Проверка, является ли карта внешней картой.
    elif map_obj.type == "external":
        return render(request, "maps/external_map.html", {"map": map_obj})

    # Проверка, является ли карта файлом.
    elif map_obj.type == "file":
        return render(
            request, "maps/external/" + map_obj.from_file.name.rsplit("/", 1)[-1]
        )

    else:
        # 404 если карта пустая
        raise Http404
