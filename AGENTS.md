# Инструкции

## Описание проекта

- Name: Ecstasy
- Backend: Python, Django, DRF (API), Celery.
- Frontend: Vue.js 3, TS, tailwindcss 4, primevue.
- Python packet manager: uv.

## Структура проекта

- `apps/` - модуль с приложениями django
- `apps/accounting/` - приложение для работы с авторизацией. Модели: UserAPIToken.
- `apps/app_settings/` - приложение с настройками приложения. Модели: LogsElasticStackSettings, ZabbixConfig, VlanTracerouteConfig, AccessRingSettings.
- `apps/check/` - основное приложение для работы с сетевым оборудованием. Модели: DeviceGroup, AuthGroup, Devices, AccessGroup, DeviceMedia, Bras, Profile, UsersActions, InterfacesComments, DeviceCommand.
- `apps/gathering/` - приложение для сбора информации с оборудований. Модели: MacAddress, Vlan, VlanPort.
- `apps/gpon/` - приложение для управления подключениями GPON и клиентами. Модели: Address, OLTState, HouseOLTState, HouseB, End3, TechCapability, Customer, Service, SubscriberConnection.
- `apps/maps/` - приложение для отображения информации на географических картах. Модели: Layers, Maps.
- `apps/net_tools/` - приложение опроса интерфейсов оборудования и построения топологии сети. Модели: DevicesInfo, DescNameFormat, VlanName, DevicesForMacSearch.
- `apps/notifications/` - приложение уведомлений. Модели: WebhookNotification, TelegramNotification, NotificationTrigger, NotificationCondition.
- `apps/ring_manager/` - приложение для определения топологии кольцо на сети. Модели: TransportRing, RingDev.
- `devicemanager/` - python модуль для работы с сетевым оборудованием
- `ecstasy_project/` - модуль django project
- `ecstasy_project/settings.py` - файл настроек django
- `frontend_v/` - папка с фронтендом приложения
- `device_connector.py` - файл для запуска device connector сервиса для подключений к сетевому оборудованию.

## Соглашения кодирования

- Используем кодировку utf-8 всегда
- Используем PEP 8
- Все функции должны иметь docstring
- Пишем тесты для backend с помощью django тестов

## Команды для тестирования

- `python manage.py test`
