from django.shortcuts import render


def page404(request, *args, **kwargs):
    """
    ## Отображает шаблон ```errors/404.html``` для любой ошибки 404
    """
    return render(request, "errors/404.html", status=404)


def page500(request, *args, **kwargs):
    """
    ## Отображает шаблон ```errors/500.html``` для любой ошибки 500
    """
    return render(request, "errors/500.html", status=500)
