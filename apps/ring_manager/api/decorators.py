from functools import wraps

from ecstasy_project.error_handler import RingOperationFailed

from ..ring_manager import InvalidRingStructureError, RingStatusError
from ..solutions import SolutionsPerformerError


def ring_valid(handler):
    """
    Декоратор перехватывает исключения «InvalidRingStructureError», «RingStatusError», «SolutionsPerformerError»
    которые могут быть вызваны функцией «handler», и возвращает ответ JSON с сообщением об ошибке
    и кодом состояния 500.
    """

    @wraps(handler)
    def wrapper(*args, **kwargs):
        try:
            return handler(*args, **kwargs)
        except (InvalidRingStructureError, RingStatusError, SolutionsPerformerError) as error:
            raise RingOperationFailed({"detail": error.message}) from error

    return wrapper
