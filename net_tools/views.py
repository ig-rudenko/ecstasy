from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def search_mac(request, mac=None):
    """ Возвращает страницу для поиска MAC адреса """
    return render(request, 'tools/search_mac.html', {'mac': mac})


@login_required
def search_description(request):
    """ Возвращает страницу для поиска порта по описанию """
    return render(request, 'tools/find_descr.html')


@login_required
def vlan_traceroute(request):
    """ Возвращает страницу для vlan traceroute """
    return render(request, 'tools/vlan_traceroute.html')




