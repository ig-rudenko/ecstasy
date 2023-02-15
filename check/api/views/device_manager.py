from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator

from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from check import models
from check.views import permission
from devicemanager.exceptions import (
    TelnetLoginError,
    TelnetConnectionError,
    UnknownDeviceError,
)
from net_tools.models import VlanName

from ..serializers import InterfacesCommentsSerializer
from ..permissions import DevicePermission


@method_decorator(permission(models.Profile.BRAS), name="dispatch")
class ChangeDescription(APIView):
    permission_classes = [DevicePermission]

    def post(self, request, device_name: str):
        """
        ## Изменяем описание на порту у оборудования
        """

        if not self.request.data.get("port"):
            raise ValidationError({"detail": "Укажите порт!"})

        dev = get_object_or_404(models.Devices, name=device_name)

        # Проверяем права доступа пользователя к оборудованию
        self.check_object_permissions(request, dev)

        new_description = self.request.data.get("description")
        port = self.request.data.get("port")

        try:
            with dev.connect() as session:
                set_description_status = session.set_description(
                    port=port, desc=new_description
                )
                new_description = session.clear_description(new_description)

        except (TelnetConnectionError, TelnetLoginError, UnknownDeviceError) as e:
            return Response({"detail": str(e)}, status=500)

        if "Неверный порт" in set_description_status:
            return Response({"detail": f"Неверный порт {port}"}, status=400)

        # Проверяем результат изменения описания
        if "Max length" in set_description_status:
            # Описание слишком длинное.
            # Находим в строке "Max length:32" число "32"
            max_length = set_description_status.split(":")[1]
            if max_length.isdigit():
                max_length = int(max_length)
            else:
                max_length = 32
            raise ValidationError(
                {
                    "detail": f"Слишком длинное описание! Укажите не более {max_length} символов."
                }
            )

        return Response({"description": new_description})


class MacListAPIView(APIView):
    permission_classes = [DevicePermission]

    def get(self, request, device_name):

        port = self.request.GET.get("port")
        if not port:
            raise ValidationError({"detail": "Укажите порт!"})

        device = get_object_or_404(models.Devices, name=device_name)
        self.check_object_permissions(request, device)

        with device.connect() as session:
            macs = []  # Итоговый список
            vlan_passed = {}  # Словарь уникальных VLAN
            for vid, mac in session.get_mac(port):  # Смотрим VLAN и MAC
                # Если еще не искали такой VLAN
                if vid not in vlan_passed:
                    # Ищем название VLAN'a
                    try:
                        vlan_name = VlanName.objects.get(vid=int(vid)).name
                    except (ValueError, VlanName.DoesNotExist):
                        vlan_name = ""
                    # Добавляем в множество вланов, которые участвовали в поиске имени
                    vlan_passed[vid] = vlan_name

                # Обновляем
                macs.append({"vlanID": vid, "mac": mac, "vlanName": vlan_passed[vid]})

        return Response({"count": len(macs), "result": macs})


class InterfaceInfoAPIView(APIView):
    permission_classes = [DevicePermission]

    def get(self, request, device_name):

        port = self.request.GET.get("port")
        if not port:
            raise ValidationError({"detail": "Укажите порт!"})

        device = get_object_or_404(models.Devices, name=device_name)
        self.check_object_permissions(request, device)

        result = {}
        with device.connect() as session:
            result["portConfig"] = session.get_port_config(port)
            result["portType"] = session.get_port_type(port)
            result["portErrors"] = session.get_port_errors(port)
            result["portDetailInfo"] = session.get_port_info(port)

        return Response(result)


class CreateInterfaceCommentAPIView(generics.CreateAPIView):
    serializer_class = InterfacesCommentsSerializer

    def perform_create(self, serializer):
        dev = get_object_or_404(models.Devices, name=self.request.data.get("device"))
        serializer.save(user=self.request.user, device=dev)


class InterfaceCommentAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.InterfacesComments.objects.all()
    serializer_class = InterfacesCommentsSerializer
    lookup_field = "pk"
    lookup_url_kwarg = "pk"
