from rest_framework.pagination import PageNumberPagination


class End3PageNumberPagination(PageNumberPagination):
    page_size = 10
