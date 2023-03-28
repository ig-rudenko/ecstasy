import datetime
import re

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views import View
from django.http.response import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.humanize.templatetags.humanize import naturaltime

from check.models import Devices
from app_settings.models import VlanTracerouteConfig
from net_tools.models import DescNameFormat
from .collectors import MacAddressTableGather
from .models import MacAddress
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


@method_decorator(login_required, name="dispatch")
class MacAddressView(View):
    def get(self, request, device_name: str):
        device = get_object_or_404(Devices, name=device_name)

        mac_gather = MacAddressTableGather(from_=device)
        mac_gather.clear_old_records()
        count = mac_gather.bulk_create()
        return JsonResponse({"mac_addresses": count})


class MacTraceroute(View):
    """
    # Находит все записи в базе данных, которые содержат необходимый MAC-адрес,
    а затем строит граф связей между этими MAC.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.desc_name_list = list(DescNameFormat.objects.all())
        # Регулярное выражение, используемое для поиска следующего устройства в описании порта.
        self.find_device_pattern = VlanTracerouteConfig.load().find_device_pattern

    def reformatting(self, name: str):
        """
        ### Форматируем строку с названием оборудования, приводя его в единый стандарт, указанный в DescNameFormat
        """

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

    @staticmethod
    def create_edge_title(mac_object: MacAddress) -> str:
        """
        ### Эта функция принимает объект MAC-адреса и возвращает строку, являющуюся заголовком ребра.
        """
        if mac_object.type == "D":
            type_ = '<div class="badge bg-primary" style="vertical-align: middle;">dynamic</div>'
        elif mac_object.type == "S":
            type_ = '<div class="badge bg-secondary" style="vertical-align: middle;">static</div>'
        elif mac_object.type == "E":
            type_ = '<div class="badge bg-warning text-dark" style="vertical-align: middle;">security</div>'
        else:
            type_ = '<div class="badge bg-light text-dark" style="vertical-align: middle;">none</div>'

        return f"""
        <div class="container py-2 rounded-2" style="font-size: 16px;">
            <p>From: <b>{mac_object.device.name}</b>; Port: <b>{mac_object.port}</b></p>
            <p>To: "<i>{mac_object.desc}</i>"</p>
            VLAN: <div class="badge bg-primary" style="vertical-align: middle;">{mac_object.vlan}</div>
            <br>Type: {type_}
            <br>Обнаружен <b>{naturaltime(mac_object.datetime)}</b>
        </div>
        """

    @staticmethod
    def create_edge_color(mac_object: MacAddress) -> str:
        """
        ### Принимает MAC-адрес и возвращает цвет ребра основываясь на типе MAC.

        :param mac_object: MAC-адрес
        """

        if mac_object.type == "D":
            return "#73beff"
        elif mac_object.type == "E":
            return "#ffbb56"

        return "#ffffff"

    def get_next_device(self, mac_address: MacAddress) -> (str, str):
        """
        ### Принимает объект mac_address и возвращает кортеж строк, где первая строка — это имя следующего устройства, а
        вторая строка — описание следующего устройства.

        :param mac_address: MacAddress — объект, содержащий MAC-адрес и описание порта, на котором он расположен.
        :return: Кортеж из двух строк.
        """
        # Ищем в описании на порту следующее устройство по паттерну
        next_device_match = re.findall(
            self.find_device_pattern, self.reformatting(mac_address.desc)
        )
        # Если нашли в описании следующее оборудование
        if next_device_match:
            next_device_id = next_device_label = next_device_match[0]

        # Если следующее устройство не найдено в описании,
        # то следующему устройству присваивается имя текущего устройства и номер порта.
        else:
            next_device_id = mac_address.device.name + mac_address.port
            next_device_label = mac_address.desc or "<no desc>"

        return next_device_id, next_device_label

    def get(self, request, mac: str):
        """
        ## Ищем MAC адрес в таблице всех MAC адресов и выстраиваем граф связей между полученными значениями.

            (D)      (C)---------(B)
             \\       /
              \\     /
               \\   /
                \\ /
                (E)---------(A)

        Отправляем список узлов и список ребер в виде ответа JSON.

        :param request: Объект запроса
        :param mac: str - MAC-адрес, который будет передан в URL
        :type mac: str
        :return: Ответ JSON, содержащий список узлов и ребер.
        """

        # Запрос, который выбирает все объекты MacAddress, имеющие MAC-адрес, переданный в URL-адресе.
        traceroute = MacAddress.objects.filter(address=mac).select_related("device")

        nodes = []
        edges = []

        # Создание списка всех устройств, которые были найдены в traceroute.
        found_devices_names = [record.device.name for record in traceroute]
        exist_nodes_id = []

        for record in traceroute:

            next_device_id, next_device_label = self.get_next_device(record)

            # Проверка отсутствия следующего устройства в списке найденных устройств и уже добавленных.
            if (
                next_device_id not in found_devices_names
                and next_device_id not in exist_nodes_id
            ):
                # Добавление нового узла в список узлов.
                nodes.append(
                    {
                        "id": next_device_id,
                        "label": next_device_label,
                        "shape": "dot",
                        "color": "green",
                    }
                )
                # Добавление следующего устройства в список существующих узлов.
                exist_nodes_id.append(next_device_id)

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

            # Он вычисляет разницу во времени между текущим временем и временем создания записи.
            time_delta = (
                datetime.datetime.now().timestamp() - record.datetime.timestamp()
            )
            # Вычисляем вес. Чем запись новее, тем больше вес.
            #         `172800` - количество секунд в двух днях.
            #         `100` - максимальный вес.
            #         `time_delta` - разница во времени между текущим временем и временем создания записи.
            k_value = int((1 - time_delta / 172800) * 100)

            # Вычисляем непрозрачность ребра. Чем больше вес, тем меньше прозрачность.
            # `hex(int(2.55 * k_value))` возвращает шестнадцатеричное строковое представление числа.
            #         `[2:]` возвращает подстроку строки, начиная с третьего символа.
            #         Например, `hex(int(2.55 * 100))` возвращает `0x64`, а `hex(int(2.55 * 100))[2:]` возвращает `64`.
            #         Это делается для того, чтобы получить шестнадцатеричное представление числа без префикса `0x`.
            opacity = hex(int(2.55 * k_value))[2:]

            # Вычисляем цвет ребра и добавляем уровень непрозрачности в шестнадцатеричном формате
            edge_color = self.create_edge_color(record) + opacity

            # Добавление нового ребра в список ребер.
            edges.append(
                {
                    "from": record.device.name,
                    "to": next_device_id,
                    "title": self.create_edge_title(record),
                    "value": k_value,
                    "color": edge_color,
                }
            )

        return JsonResponse({"nodes": nodes, "edges": edges})
