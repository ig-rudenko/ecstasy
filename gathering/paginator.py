from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import connection


class LargeTablePaginator(Paginator):
    """Переопределяет метод подсчета, чтобы получить оценку вместо фактического подсчета, если он не отфильтрован."""

    _count = None  # Кэш кол-ва записей, по умолчанию значение отсутствует
    _limit = 10_000  # Предел для быстрого поиска
    _standard_count = False  # Точный поиск уже был сделан?

    def validate_number(self, number):
        try:
            number = int(number)
        except (TypeError, ValueError):
            number = 1

        # Если значение подошло к 0.9 от всех записей, то включаем точный подсчет
        if not self._standard_count and (number * self.per_page) > self.count * 0.9:
            self._standard_count = True
            self._count = self.object_list.count()

        if number < 1:
            number = 1
        elif number > self.num_pages:
            if number == 1 and self.allow_empty_first_page:
                pass
            else:
                number = self.num_pages
        return number

    @staticmethod
    def _get_database_engine() -> str:
        return str(settings.DATABASES["default"]["ENGINE"]).rsplit(".", 1)[1]

    def _get_table_count(self) -> int:
        table_name = self.object_list.query.model._meta.db_table  # type: ignore
        engine = self._get_database_engine()

        with connection.cursor() as cursor:
            if engine == "postgresql":
                cursor.execute(
                    "SELECT reltuples::BIGINT AS estimate FROM pg_class WHERE relname = %s", [table_name]
                )
                row = cursor.fetchone()
                return int(row[0]) if row and row[0] is not None else 0

            elif engine in ("mysql", "mariadb"):
                cursor.execute("SHOW TABLE STATUS WHERE Name = %s", [table_name])
                row = cursor.fetchone()
                if row:
                    # Rows count is usually at index 4, but we can also use column names for clarity
                    desc = cursor.description
                    columns = {col[0]: idx for idx, col in enumerate(desc)}
                    rows_index = columns.get("Rows", 4)
                    return int(row[rows_index]) if row[rows_index] is not None else 0

        return 0

    def _get_estimate(self) -> int:
        if not self.object_list.query.where:  # type: ignore
            try:
                return self._get_table_count()
            except Exception as error:  # pylint: disable=W0703
                print(self.__class__.__name__, error)
        return 0

    @property
    def count(self):  # pylint: disable=W0236
        """Если быстрый подсчет дал менее 10 000 записей, то возвращает общее количество объектов"""
        if self._count is None:
            try:
                estimate = self._get_estimate()
                if estimate < self._limit:
                    # Записи не превысили лимит для точного поиска, запускаем его
                    self._standard_count = True
                    self._count = self.object_list.count()
                else:
                    self._count = estimate
            except (AttributeError, TypeError):
                # AttributeError if object_list has no count() method.
                # TypeError if object_list.count() requires arguments
                # (i.e. is of type list).
                self._count = self.object_list.count()

        return self._count


class CachedLargeTablePaginator(LargeTablePaginator):
    CACHE_TIMEOUT = 60 * 2

    def _cache_key(self) -> str:
        db_alias = self.object_list.db if hasattr(self.object_list, "db") else "default"
        table_name = self.object_list.query.model._meta.db_table  # type: ignore
        return f"table_count_estimate:{db_alias}:{table_name}"

    def _get_table_count(self):
        key = self._cache_key()
        cached = cache.get(key)
        if cached is not None:
            return cached

        data = super()._get_table_count()
        if data:
            if data > self._limit:
                cache.set(key, data, timeout=self.CACHE_TIMEOUT)
            return data

        return 0
