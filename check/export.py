"""
Модуль предоставляет функциональность для создания Excel-файлов на основе переданной выборки из модели.
"""

import orjson
import xlwt
from django.db.models import QuerySet
from django.http import HttpResponse
from django.utils import timezone

from devicemanager.device import Interfaces


# pylint: disable=maybe-no-member, missing-function-docstring


class ExcelExport:
    """
    Предоставляет функциональность для создания Excel-файлов на основе переданной выборки из модели.

    Для каждого поля, участвующего в формировании выборки `queryset_values`, необходимо реализовать
    соответствующий метод извлечения данных из полученного результата queryset, который будет
    называться `get_<field_name>`.

    Для каждого поля соответствующий метод должен вернуть словарь, где ключом будет название колонки,
    excel, одной или несколько, из перечня `excel_headers`.

    Класс также предоставляет методы для записи заголовков столбцов и строк, последней строки с общим
    количеством значений для некоторых колонок.
    """

    # Список полей из queryset, которые будут использоваться для формирования выборки.
    queryset_values: list[str] = []

    # Список полей, которые будут использоваться для формирования join запроса,
    # с целью оптимизации скорости выборки.
    select_related: list[str] = []

    excel_headers: list[str] = []  # Список заголовков столбцов excel файла.
    sheet_name = "data"  # имя листа в excel файле.

    def __init__(self, queryset: QuerySet):
        for select_related_field in self.select_related:
            queryset = queryset.select_related(select_related_field)

        # Формируем данные
        self._queryset: QuerySet = queryset.values(*self.queryset_values)

        # Создаем excel
        self._wb = xlwt.Workbook()
        self._sheet = self._wb.add_sheet(self.sheet_name)

        # Словарь в который можно помещать значения некоторых колонок для суммирования значений
        self.total: dict[str, int] = {}

    @staticmethod
    def get_file_name() -> str:
        return f"interfaces_{timezone.now().strftime('%Y.%m.%d_%H.%M.%S')}.xls"

    def _create_workbook_headers(self) -> None:
        """Запись заголовков столбцов excel файла."""
        for column_index, header_name in enumerate(self.excel_headers):
            self._sheet.write(0, column_index, header_name)

    def write_total_row(self, to_row: int) -> None:
        """
        Запись последней строки в excel файле,
        в которой будут отображаться значения для некоторых колонок.
        """
        for column_name, total_value in self.total.items():
            self._sheet.write(to_row, self.excel_headers.index(column_name), f"Всего: {total_value}")

    def _get_query_value_data(self, query_data: dict, value: str) -> dict:
        return getattr(self, f"get_{value}")(query_data)

    def make_excel(self):
        """Создание excel структуры файла на основе выборки и указанных полей."""

        self._create_workbook_headers()

        row = 1

        # Проходимся по элементам (строчки `queryset`)
        for query_element in self._queryset:
            # По очереди необходимо обработать ключи каждого элемента (столбцы)
            for query_value in self.queryset_values:
                # Имеется ли метод для обработки этого ключа элемента
                if not hasattr(self, f"get_{query_value}"):
                    continue

                data = self._get_query_value_data(query_element, query_value)

                for column_name, column_value in data.items():
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
    """
    Наследуется от ExcelExport и расширяет его функциональность требуемой логикой, связанной
    с выборкой интерфейсных данных устройств.

    Реализует метод для создания HTTP-ответа в виде excel файла.
    """

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
        """
        Получение количества интерфейсов,
        абонентских портов и задействованных абонентских портов устройства.
        """
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
        """Создание HTTP-ответа в виде excel файла."""

        response = HttpResponse(content_type="application/vnd.ms-excel")
        response["Content-Disposition"] = f"attachment; filename={self.get_file_name()}"
        self._wb.save(response)
        return response
