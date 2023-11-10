from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render


@login_required
def main_rings_view(request):
    return render(request, "ring-manager/index.html")


@login_required
@permission_required(perm="auth.access_transport_rings", raise_exception=True)
def transport_rings_view(request):
    return render(request, "ring-manager/transport_rings.html")


@login_required
@permission_required(perm="auth.access_rings", raise_exception=True)
def access_rings_view(request):
    return render(request, "ring-manager/access_rings.html")
