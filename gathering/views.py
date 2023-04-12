from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http.response import JsonResponse, HttpResponse
from .tasks import mac_table_gather_task, check_scanning_status


@login_required
def run_macs_scan(request):
    """
    Запускаем задачу на сбор MAC адресов в таблицах оборудований.
    """

    if request.method == "POST":
        task_id = cache.get("mac_table_gather_task_id")
        if not task_id:
            task_id = mac_table_gather_task.delay()
            cache.set("mac_table_gather_task_id", task_id, timeout=None)
            return HttpResponse(status=200)

    return JsonResponse({}, status=400)


@login_required
def check_periodically_scan(request):
    """
    ## Проверяет, выполняется ли сканирование, и если да, то возвращает результаты.
    """
    return JsonResponse(check_scanning_status())
