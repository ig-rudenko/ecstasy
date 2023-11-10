from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render


@login_required
@permission_required(perm="auth.access_wtf_search", raise_exception=True)
def search_wtf_is_it(request, mac=None):
    """Возвращает страницу для поиска MAC адреса"""
    return render(request, "tools/search_mac.html", {"mac": mac})


@login_required
@permission_required(perm="auth.access_desc_search", raise_exception=True)
def search_description(request):
    """Возвращает страницу для поиска порта по описанию"""
    return render(request, "tools/find_descr.html")


@login_required
@permission_required(perm="auth.access_traceroute", raise_exception=True)
def traceroute(request):
    """Возвращает страницу для traceroute"""
    return render(request, "tools/traceroute.html")
