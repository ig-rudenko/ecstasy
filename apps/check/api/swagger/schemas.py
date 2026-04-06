from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from ...api.serializers import DevicesSerializer, MacSerializer, PortControlSerializer
from .query_params import DeviceInterfacesQueryParamsSerializer
from .requests import (
    ChangeDescriptionRequestSwaggerSerializer,
    ExecuteBulkDeviceCommandRequestSwaggerSerializer,
)
from .responses import (
    BrasPairSessionResultSwaggerSerializer,
    BulkCommandLaunchResponseSwaggerSerializer,
    BulkCommandTaskStatusSwaggerSerializer,
    ChangeDescriptionSwaggerSerializer,
    ConfigFileSwaggerSerializer,
    CutBrasSessionSwaggerSerializer,
    DeviceInfoSwaggerSerializer,
    DevicePoolStatusesSwaggerSerializer,
    DevicesConfigListSwaggerSerializer,
    DevicesInterfaceWorkloadResultSwaggerSerializer,
    InterfaceDetailInfoSwaggerSerializer,
    InterfacesListSwaggerSerializer,
    InterfaceWorkloadSwaggerSerializer,
    MacListResultSwaggerSerializer,
    device_unavailable,
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


devices_list_api_doc = swagger_auto_schema(
    # query_serializer=DeviceQueryParamsSerializer(),
    responses={
        200: DevicesSerializer(many=True),
    },
)

devices_interfaces_workload_list_api_doc = swagger_auto_schema(
    responses={
        200: DevicesInterfaceWorkloadResultSwaggerSerializer(),
    },
)


interfaces_workload_api_doc = swagger_auto_schema(
    responses={
        200: InterfaceWorkloadSwaggerSerializer(),
    }
)


interfaces_list_api_doc = swagger_auto_schema(
    query_serializer=DeviceInterfacesQueryParamsSerializer(),
    responses={
        200: InterfacesListSwaggerSerializer(),
    },
)

device_info_api_doc = swagger_auto_schema(
    responses={
        200: DeviceInfoSwaggerSerializer(),
    }
)

mac_list_api_doc = swagger_auto_schema(
    manual_parameters=[
        openapi.Parameter(
            "port",
            openapi.IN_QUERY,
            description="Порт (интерфейс) оборудования",
            type=openapi.TYPE_STRING,
            required=True,
        ),
    ],
    responses={
        200: MacListResultSwaggerSerializer(),
    },
)

interface_info_api_doc = swagger_auto_schema(
    responses={
        200: InterfaceDetailInfoSwaggerSerializer(),
    }
)


change_dsl_profile_api_doc = swagger_auto_schema(
    responses={
        200: openapi.Response(
            description="Результат изменения",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "status": openapi.Schema(
                        type=openapi.TYPE_STRING,
                    )
                },
            ),
        ),
        400: openapi.Response(
            description="Device can't change profile",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "detail": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="Device can't change profile",
                    )
                },
            ),
        ),
        500: device_unavailable,
    }
)


change_description_api_doc = swagger_auto_schema(
    request_body=ChangeDescriptionRequestSwaggerSerializer(),
    responses={
        200: ChangeDescriptionSwaggerSerializer(),
    },
)

bras_get_session_api_doc = swagger_auto_schema(
    query_serializer=MacSerializer(),
    responses={
        200: BrasPairSessionResultSwaggerSerializer(),
    },
)

cut_bras_session_api_doc = swagger_auto_schema(
    responses={
        200: CutBrasSessionSwaggerSerializer(),
    }
)


set_device_viewings_api_doc = swagger_auto_schema(request_body=None, responses={200: ""})


get_device_pool_status_api_doc = swagger_auto_schema(responses={200: DevicePoolStatusesSwaggerSerializer()})


execute_bulk_device_command_api_doc = swagger_auto_schema(
    request_body=ExecuteBulkDeviceCommandRequestSwaggerSerializer(),
    responses={
        202: BulkCommandLaunchResponseSwaggerSerializer(),
        400: "Bad Request",
        403: "Permission denied",
        404: "Command not found",
    },
)


bulk_device_command_task_status_api_doc = swagger_auto_schema(
    responses={
        200: BulkCommandTaskStatusSwaggerSerializer(),
        403: "Permission denied",
    },
)
