from . import models
from .logger import django_actions_logger


def log(user: models.User, model_device: (models.Devices, models.Bras), operation: str):
    """
    ## Записывает логи о действиях пользователя

    :param user: Пользователь, который совершил действие
    :param model_device: Оборудование, по отношению к которому было совершено действие
    :param operation: Описание действия
    :return: None
    """

    # Проверка того, НЕ является ли пользователь экземпляром класса models.User
    # или model_device НЕ является экземпляром класса models.Devices или models.Bras,
    # или операция НЕ является строкой.
    if (
        not isinstance(user, models.User)
        or not isinstance(model_device, (models.Devices, models.Bras))
        or not isinstance(operation, str)
    ):
        django_actions_logger.info(
            f"| NO DB | {str(user):<10} | {str(model_device):<15} | {str(operation)}\n"
        )
        return

    # В базу
    # Получение максимальной длины поля «действие» в модели UsersActions.
    operation_max_length = models.UsersActions._meta.get_field("action").max_length
    if len(operation) > operation_max_length:
        operation = operation[:operation_max_length]

    # Проверка того, является ли model_device экземпляром класса models.Devices.
    if isinstance(model_device, models.Devices):
        models.UsersActions.objects.create(
            user=user, device=model_device, action=operation
        )
        # В файл
        django_actions_logger.info(
            f"| {user.username:<10} | {model_device.name} ({model_device.ip}) | {operation}\n"
        )

    else:
        # В базу
        models.UsersActions.objects.create(
            user=user, action=f"{model_device} | " + operation
        )
        # В файл
        django_actions_logger.info(
            f"| {user.username:<10} |  | {model_device} | {operation}\n"
        )
