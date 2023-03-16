from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def search_wtf_is_it(request, mac=None):
    """Возвращает страницу для поиска MAC адреса"""
    return render(request, "tools/search_mac.html", {"mac": mac})


@login_required
def search_description(request):
    """Возвращает страницу для поиска порта по описанию"""
    return render(request, "tools/find_descr.html")


@login_required
def traceroute(request):
    """Возвращает страницу для traceroute"""
    return render(request, "tools/traceroute.html")
