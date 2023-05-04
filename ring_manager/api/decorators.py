from functools import wraps

from rest_framework.response import Response
from rest_framework import status

from ..ring_manager import InvalidRingStructureError, RingStatusError


def ring_valid(handler):
    """
    Декоратор перехватывает любые исключения «InvalidRingStructureError» или «RingStatusError»,
    которые могут быть вызваны функцией «обработчик», и возвращает ответ JSON с сообщением об ошибке
    и кодом состояния 500.
    """

    @wraps(handler)
    def wrapper(*args, **kwargs):
        try:
            return handler(*args, **kwargs)
        except (InvalidRingStructureError, RingStatusError) as error:
            return Response({"error": error.message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return wrapper
