import xlwt
import orjson
from django.db.models import QuerySet
from django.http import HttpResponse
from django.utils import timezone

from devicemanager.device import Interfaces
from .models import Devices


class ExcelExport:
    queryset_values = []
    select_related = []
    excel_headers = []
    sheet_name = "data"

    def __init__(self, queryset: QuerySet[Devices]):
        for select_related_field in self.select_related:
            queryset = queryset.select_related(select_related_field)

        # Формируем данные
        self._queryset: QuerySet[dict] = queryset.values(
            *self.queryset_values
        )

        # Создаем excel
        self._wb = xlwt.Workbook()
        self._sheet = self._wb.add_sheet(self.sheet_name)

        # Словарь в который можно помещать значения некоторых колонок для суммирования значений
        self.total = dict()

    @staticmethod
    def get_file_name():
        return f"interfaces_{timezone.now().strftime('%Y.%m.%d_%H.%M.%S')}.xls"

    def _create_workbook_headers(self):
        for i, h in enumerate(self.excel_headers):
            self._sheet.write(0, i, h)

    def write_total_row(self, to_row: int):
        for column_name, total_value in self.total.items():
            self._sheet.write(to_row, self.excel_headers.index(column_name), f"Всего: {total_value}")

    def make_excel(self):
        self._create_workbook_headers()

        row = 1

        # Проходимся по элементам (строчки `queryset`)
        for query_element_data in self._queryset:

            # По очереди необходимо обработать ключи каждого элемента (столбцы)
            for query_value in self.queryset_values:

                # Имеется ли метод для обработки этого ключа элемента
                if not hasattr(self, f"get_{query_value}"):
                    continue

                for column_name, column_value in getattr(self, f"get_{query_value}")(query_element_data).items():
                    # Смотрим какие названия колонок были возвращены, а также их значения
                    # Ведь для одного поля элемента `queryset` может быть возвращено несколько значений для
                    # колонок excel файла.

                    # Находим индекс колонки excel.
                    column_index = self.excel_headers.index(column_name)
                    # Записываем туда значение.
                    self._sheet.write(row, column_index, column_value)

            # Теперь следующая строчка
            row += 1

        # Записываем последнюю строчку общего кол-ва
        self.write_total_row(to_row=row)


class DevicesInterfacesWorkloadExcelExport(ExcelExport):
    queryset_values = ["ip", "name", "vendor", "model", "devicesinfo__interfaces"]
    excel_headers = [
        "IP",
        "Название оборудования",
        "Производитель",
        "Модель",
        "Кол-во всех интерфейсов",
        "Кол-во всех абонентских портов",
        "Кол-во задействованных абонентских портов",
    ]
    select_related = ["devicesinfo"]

    @staticmethod
    def get_ip(query_element: dict):
        return {"IP": query_element.get("ip")}

    @staticmethod
    def get_name(query_element: dict):
        return {"Название оборудования": query_element.get("name")}

    @staticmethod
    def get_vendor(query_element: dict):
        return {"Производитель": query_element.get("vendor")}

    @staticmethod
    def get_model(query_element: dict):
        return {"Модель": query_element.get("model")}

    def get_devicesinfo__interfaces(self, query_element: dict):
        interfaces = Interfaces(orjson.loads(query_element.get("devicesinfo__interfaces") or "[]"))

        interfaces = interfaces.physical()

        non_system = interfaces.non_system()
        abons_up = non_system.up()

        data = {
            "Кол-во всех интерфейсов": interfaces.count,
            "Кол-во всех абонентских портов": non_system.count,
            "Кол-во задействованных абонентских портов": abons_up.count,
        }

        for column_name, value in data.items():
            if not self.total.get(column_name):
                self.total[column_name] = 0
            self.total[column_name] += value

        return data

    def create_response(self) -> HttpResponse:
        response = HttpResponse(content_type="application/vnd.ms-excel")
        response["Content-Disposition"] = f"attachment; filename={self.get_file_name()}"
        self._wb.save(response)
        return response
