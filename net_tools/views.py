from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from net_tools.finder import get_stat


@login_required
def search_mac(request, mac=None):
    """ Возвращает страницу для поиска MAC адреса """

    return render(request, 'tools/search_mac.html', {'mac': mac})


@login_required
def search_description(request):
    """ Возвращает страницу для поиска порта по описанию """

    devs_count, intf_count = get_stat('interfaces')
    return render(
        request,
        'tools/find_descr.html',
        {
            "devs_count": devs_count,
            'intf_count': intf_count or 'None'
        }
    )


@login_required
def vlan_traceroute(request):

    devs_count, intf_count = get_stat('vlans')
    return render(
        request,
        'tools/vlan_traceroute.html',
        {
            "devs_count": devs_count,
            'intf_count': intf_count,
            'percent': str(round(
                intf_count/devs_count if devs_count else 0,
                3
            ))
        }
    )




