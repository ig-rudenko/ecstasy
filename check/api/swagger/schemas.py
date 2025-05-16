from drf_yasg.utils import swagger_auto_schema

from check.api.serializers import PortControlSerializer
from .responses import (
    DevicesConfigListSwaggerSerializer,
    ConfigFileSwaggerSerializer,
    DevicesInterfaceWorkloadSwaggerSerializer,
    InterfaceWorkloadSwaggerSerializer,
    InterfacesListSwaggerSerializer,
    DeviceInfoSwaggerSerializer,
)

# Изменяем состояние порта оборудования
port_control_api_doc = swagger_auto_schema(
    responses={
        200: PortControlSerializer(),
        400: "Bad Request",
        403: "У вас недостаточно прав, для изменения состояния порта!\n"
        "Запрещено изменять состояние данного порта!",
        500: "Неизвестный тип оборудования\nНеверный Логин/Пароль\nTelnet недоступен",
    }
)


devices_config_files_list_api_doc = swagger_auto_schema(
    responses={
        200: DevicesConfigListSwaggerSerializer(),
    }
)


config_files_list_api_doc = swagger_auto_schema(
    responses={
        200: ConfigFileSwaggerSerializer(many=True),
    }
)


devices_interfaces_workload_list_api_doc = swagger_auto_schema(
    responses={
        200: DevicesInterfaceWorkloadSwaggerSerializer(many=True),
    }
)


interfaces_workload_api_doc = swagger_auto_schema(
    responses={
        200: InterfaceWorkloadSwaggerSerializer(),
    }
)


interfaces_list_api_doc = swagger_auto_schema(
    responses={
        200: InterfacesListSwaggerSerializer(),
    }
)

device_info_api_doc = swagger_auto_schema(
    responses={
        200: DeviceInfoSwaggerSerializer(),
    }
)
