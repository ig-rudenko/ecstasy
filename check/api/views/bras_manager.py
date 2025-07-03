from django.utils.decorators import method_decorator
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from check import models
from check.permissions import profile_permission
from check.services.bras import cut_bras_session, get_bras_sessions
from ecstasy_project.types.api import UserAuthenticatedAPIView
from ..permissions import DevicePermission
from ..serializers import BrassSessionSerializer, MacSerializer
from ..swagger.schemas import cut_bras_session_api_doc, bras_get_session_api_doc


class BrassSessionAPIView(UserAuthenticatedAPIView):
    @method_decorator(bras_get_session_api_doc)
    @method_decorator(profile_permission(models.Profile.BRAS))
    def get(self, request):
        """
        ## Возвращаем сессию на BRAS для конкретного MAC адреса

        Пример ответа:

            {
                "BRAS1": {
                    "session": null,
                    "errors": [
                        "Не удалось подключиться"
                    ]
                },
                "BRAS2": {
                    "session": " ... ",
                    "errors": []
                }
            }
        """

        serializer = MacSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        result = get_bras_sessions(serializer.validated_data["mac"])

        return Response(result)


class CutBrassSessionAPIView(UserAuthenticatedAPIView):
    """
    ## Сбрасываем сессию по MAC адресу и перезагружаем порт на оборудовании
    """

    permission_classes = [IsAuthenticated, DevicePermission]
    serializer_class = BrassSessionSerializer

    @method_decorator(cut_bras_session_api_doc)
    @method_decorator(profile_permission(models.Profile.BRAS))
    def post(self, request):
        """
        ## Сбрасываем сессию абонента и перезагружаем порт на оборудовании

        Данные формы:

        - str:`mac` - max:24
        - str:`device` - max:255
        - str:`port` - max:50

        Сбрасываем сессию и перезагружаем порт на оборудовании

        Возвращаем:

            {
                "portReloadStatus": "RELOAD STATUS",
                "errors": []
            }
        """

        serializer = BrassSessionSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        # Берем mac-адрес из формы и форматируем его в строку вида `aaaa-bbbb-cccc`.
        mac = serializer.validated_data["mac"]
        port = serializer.validated_data["port"]
        device = get_object_or_404(models.Devices, name=serializer.validated_data["device"])
        self.check_object_permissions(self.request, device)

        result = cut_bras_session(device, self.current_user, mac, port)
        return Response(result)
