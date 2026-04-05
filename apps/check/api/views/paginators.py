from rest_framework.pagination import PageNumberPagination


class End3PageNumberPagination(PageNumberPagination):
    page_size = 10


class BulkDeviceCommandExecutionPagination(PageNumberPagination):
    """Pagination for persisted bulk command history."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class BulkDeviceCommandExecutionResultPagination(PageNumberPagination):
    """Pagination for persisted device results inside one bulk execution."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
