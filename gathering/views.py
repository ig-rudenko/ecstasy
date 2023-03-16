import re

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.views import View
from django.http.response import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404

from check.models import Devices
from app_settings.models import VlanTracerouteConfig
from net_tools.models import DescNameFormat
from .collectors import GatherMacAddressTable
from .models import MacAddress
from .tasks import mac_table_gather_task, check_scanning_status


@login_required
def run_periodically_scan(request):

    if request.method == "POST":
        task_id = cache.get("mac_table_gather_task_id")
        if not task_id:
            task_id = mac_table_gather_task.delay()
            cache.set("mac_table_gather_task_id", task_id, timeout=None)
            return HttpResponse(status=200)

    return JsonResponse({}, status=400)


@login_required
def check_periodically_scan(request):
    return JsonResponse(check_scanning_status())


class MacAddressView(View):
    def get(self, request, device_name: str):
        device = get_object_or_404(Devices, name=device_name)

        mac_gather = GatherMacAddressTable(from_=device)
        mac_gather.clear_old_records()
        count = mac_gather.bulk_create()
        return JsonResponse({"mac_addresses": count})


class MacTraceroute(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.desc_name_list = list(DescNameFormat.objects.all())

    def reformatting(self, name: str):
        """Форматируем строку с названием оборудования, приводя его в единый стандарт, указанный в DescNameFormat"""

        for reformat in self.desc_name_list:
            if reformat.standard == name:
                # Если имя совпадает с правильным, то отправляем его
                return name

            for pattern in reformat.replacement.split(", "):
                if pattern in name:  # Если паттерн содержится в исходном имени

                    # Заменяем совпадение "pattern" в названии "name" на правильное "n"
                    return re.sub(pattern, reformat.standard, name)

        # Если не требуется замены
        return name

    def get(self, request, mac: str):
        # Запрос, который выбирает все объекты MacAddress, имеющие MAC-адрес, переданный в URL-адресе.
        traceroute = MacAddress.objects.filter(address=mac).select_related("device")

        # Регулярное выражение, используемое для поиска следующего устройства в описании порта.
        find_device_pattern = VlanTracerouteConfig.load().find_device_pattern
        nodes = []
        edges = []

        # Создание списка всех устройств, которые были найдены в traceroute.
        found_devices_names = [record.device.name for record in traceroute]
        exist_nodes_id = []

        for record in traceroute:

            # Ищем в описании на порту следующее устройство по паттерну
            next_device = re.findall(
                find_device_pattern, self.reformatting(record.desc)
            )
            next_device = next_device[0] if next_device else record.desc

            # Проверка отсутствия следующего устройства в списке найденных устройств и уже добавленных.
            if (
                next_device not in found_devices_names
                and next_device not in exist_nodes_id
            ):
                # Добавление нового узла в список узлов.
                nodes.append(
                    {
                        "id": next_device,
                        "label": next_device,
                        "shape": "dot",
                        "color": "green",
                    }
                )
                # Добавление следующего устройства в список существующих узлов.
                exist_nodes_id.append(next_device)

            # Проверка наличия имени устройства в списке созданных узлов.
            if record.device.name not in exist_nodes_id:
                # Добавление нового узла в список узлов.
                nodes.append(
                    {
                        "id": record.device.name,
                        "label": record.device.name,
                        "shape": "dot",
                    }
                )
                # Добавление имени устройства в список существующих узлов.
                exist_nodes_id.append(record.device.name)

            # Добавление нового ребра в список ребер.
            edges.append(
                {
                    "from": record.device.name,
                    "to": next_device,
                    "title": f"From {record.device.name}; Port {record.port}\n",
                }
            )

        return JsonResponse({"nodes": nodes, "edges": edges})
