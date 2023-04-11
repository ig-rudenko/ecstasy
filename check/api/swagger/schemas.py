from drf_yasg.utils import swagger_auto_schema

from check.api.serializers import PortControlSerializer

from .responses import DevicesConfigListSwaggerSerializer, ConfigFileSwaggerSerializer

# Изменяем состояние порта оборудования
port_control_api_doc = swagger_auto_schema(
    responses={
        200: PortControlSerializer(),
        400: "Bad Request",
        403: "У вас недостаточно прав, для изменения состояния порта!\n"
        "Запрещено изменять состояние данного порта!",
        500: "Неизвестный тип оборудования\n"
        "Неверный Логин/Пароль\n"
        "Telnet недоступен",
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
