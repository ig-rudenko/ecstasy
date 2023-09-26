from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def gpon_home(request):
    return render(request, "gpon/main.html")
