import re
from concurrent.futures import ThreadPoolExecutor

import pexpect
from django.utils.decorators import method_decorator
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from check.views import log, permission
from ..permissions import DevicePermission
from check import models
from devicemanager.exceptions import (
    TelnetConnectionError,
    TelnetLoginError,
    UnknownDeviceError,
)
from ..serializers import BrassSessionSerializer, MacSerializer


def get_user_session(bras: models.Bras, mac: str, result: dict):
    """
    ## Получает сеанс пользователя для заданного MAC-адреса.

    :param bras: объект Bras, к которому подключается пользователь
    :param mac: мак адрес пользователя
    :param result: dict, содержащий информацию о сессии
    """

    result[bras.name] = {"session": None, "errors": []}

    try:
        with bras.connect() as session:
            bras_output = session.send_command(f"display access-user mac-address {mac}", expect_command=False)
            if "No online user!" not in bras_output:
                user_index = re.findall(r"User access index\s+:\s+(\d+)", bras_output)

                if user_index:
                    bras_output = session.send_command(
                        f"display access-user user-id {user_index[0]} verbose",
                    )

            result[bras.name]["session"] = bras_output

    except TelnetConnectionError:
        result[bras.name]["errors"].append("Не удалось подключиться к " + bras.name)
    except TelnetLoginError:
        result[bras.name]["errors"].append("Неверный Логин/Пароль " + bras.name)
    except UnknownDeviceError:
        result[bras.name]["errors"].append("Неизвестные тип оборудования " + bras.name)


@method_decorator(permission(models.Profile.BRAS), name="get")
class BrassSessionAPIView(APIView):
    def get(self, request):
        serializer = MacSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        # Берем mac-адрес из формы и форматируем его в строку вида `aaaa-bbbb-cccc`.
        mac = models.Bras.format_mac(serializer.validated_data["mac"])

        result = {}

        with ThreadPoolExecutor() as executor:
            for bras in models.Bras.objects.all():
                # Приведенный выше код создает пул потоков,
                # а затем отправляет функцию get_user_session в пул потоков.
                executor.submit(get_user_session, bras, mac, result)

        return Response(result)


@method_decorator(permission(models.Profile.BRAS), name="post")
class CutBrassSessionAPIView(APIView):
    permission_classes = [DevicePermission]

    def post(self, request):
        serializer = BrassSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Берем mac-адрес из формы и форматируем его в строку вида `aaaa-bbbb-cccc`.
        mac = models.Bras.format_mac(serializer.validated_data["mac"])
        device = get_object_or_404(
            models.Devices, name=serializer.validated_data["device"]
        )
        self.check_object_permissions(request, device)

        # Словарь, который будет содержать данные для отправки
        result = {"errors": []}

        for bras in models.Bras.objects.all():
            try:
                with bras.connect() as session:
                    session.send_command("system-view")
                    session.send_command("aaa")
                    # Срезаем сессию по MAC адресу
                    session.send_command(f"cut access-user mac-address {mac}")
                    # Логи
                    log(request.user, device, f"cut access-user mac-address {mac}")

            except pexpect.TIMEOUT:
                result["errors"].append(f"{bras.name} - timeout")  # Был недоступен

        try:
            with device.connect() as session:
                # Перезагружаем порт без сохранения конфигурации
                reload_port_status = session.reload_port(
                    serializer.validated_data["port"], save_config=False
                )

                result["portReloadStatus"] = reload_port_status  # Успех

                # Логи
                log(
                    request.user,
                    device,
                    f"reload port {serializer.validated_data['port']} \n"
                    f"{reload_port_status}",
                )

        except (TelnetConnectionError, TelnetLoginError, UnknownDeviceError) as e:
            result["errors"].append(
                f"Сессия сброшена, но порт не был перезагружен! {e}"
            )

        return Response(result)
