# Инструкции для агентов

## Общие правила

- Всегда отвечать пользователю на русском языке.
- Всегда использовать UTF-8.
- Перед изменениями читать связанные исходники, тесты и конфигурацию.
- Не отменять и не перезаписывать изменения пользователя в грязном рабочем дереве.
- Вносить только изменения, необходимые для текущей задачи; не выполнять попутный рефакторинг.
- Не редактировать сгенерированные файлы и каталоги: `frontend_v/node_modules/`, `frontend_v/dist/`, `__pycache__/`, `*.pyc`.
- Не добавлять в репозиторий секреты и значения из локального `.env`.

## Описание проекта

- Name: Ecstasy (Equipment Control System To Assist You).
- Назначение: веб-приложение для управления сетевым оборудованием, сбора данных, поиска и визуализации сетевой информации.
- Backend: Python 3.12+, Django, Django REST Framework, Celery.
- Frontend: Vue.js 3, TypeScript, Vite, Tailwind CSS 4, PrimeVue 4, Vue Router, Vuex.
- Хранилища и инфраструктура: MySQL, Redis, Nginx, Docker Compose.
- Python package manager: `uv`. Виртуальное окружение находится в `.venv`.
- Версия проекта задаётся одновременно в `pyproject.toml`, `frontend_v/package.json` и образах в `docker-compose.yaml`.

## Архитектура

Основной поток веб-запроса:

1. Vue SPA обращается к относительным URL `/api/...`.
2. В dev-режиме Vite проксирует `/api` на `http://127.0.0.1:8000`.
3. В Docker Nginx отдаёт SPA и проксирует `/api`, `/admin`, `/oidc`, `/media`, `/static` в Django.
4. Django DRF обрабатывает API под префиксом `/api/v1/`.

Поток работы с сетевым оборудованием:

1. Django-приложения используют `devicemanager`.
2. `devicemanager/remote/connector.py` обращается к отдельному Flask-сервису по `DEVICE_CONNECTOR_ADDRESS`.
3. `device_connector.py` выполняет методы драйверов оборудования через SSH, Telnet или SNMP и управляет пулами сессий.
4. Вендорская логика и TextFSM-шаблоны находятся в `devicemanager/vendors/` и `devicemanager/templates/`.

Фоновые задачи:

- Celery автоматически находит задачи в `apps/*/tasks.py`.
- Redis используется как broker/result backend и, при наличии `REDIS_CACHE_URL`, как Django cache.
- Периодические задачи запускает `celery-beat` с `django_celery_beat.schedulers:DatabaseScheduler`.
- В `DJANGO_ENV=dev` задачи Celery по умолчанию выполняются eager, если `CELERY_TASK_ALWAYS_EAGER` не переопределён.

База данных:

- При наличии `MYSQL_DATABASE` Django использует MySQL.
- Без `MYSQL_DATABASE` используется локальная SQLite-база `db.sqlite3`.

## Основные точки входа

- `manage.py` — Django management.
- `ecstasy_project/settings.py` — настройки Django, DRF, Celery, cache, Keycloak и хранилищ.
- `ecstasy_project/urls.py` — корневые URL, API, JWT, Swagger/Redoc и protected media.
- `ecstasy_project/celery.py` — Celery application.
- `device_connector.py` — Flask API для подключений к оборудованию.
- `frontend_v/src/main.ts` — инициализация Vue, PrimeVue, store, router и OIDC.
- `frontend_v/src/router.ts` — маршруты SPA и проверка авторизации.
- `frontend_v/src/services/` — HTTP-клиенты и клиентская бизнес-логика.
- `docker-compose.yaml` — frontend, backend, Celery worker, Celery beat, device connector, Redis и MySQL.
- `nginx/default.conf` — раздача SPA и reverse proxy.

## Django-приложения

Активные Django-приложения определяются списком `INSTALLED_APPS` в `ecstasy_project/settings.py`; наличие каталога в `apps/` само по себе не означает, что приложение подключено.

- `apps/accounting/` — текущий пользователь, permissions, API-токены и OIDC-конфигурация. Модель: `UserAPIToken`.
- `apps/app_settings/` — singleton-настройки приложения. Модели: `LogsElasticStackSettings`, `ZabbixConfig`, `TracerouteConfig`, `AccessRingSettings`.
- `apps/check/` — основной домен оборудования, интерфейсов, авторизации, команд, конфигураций и массового выполнения команд. API: `/api/v1/devices/`.
- `apps/discovery/` — автоматическое обнаружение оборудования: профили, запуски, кандидаты, fingerprint и provisioning. API: `/api/v1/discovery/`.
- `apps/gathering/` — собранные MAC-адреса, VLAN и порты VLAN. API: `/api/v1/gather/`.
- `apps/gpon/` — адреса, GPON-топология, техническая возможность, клиенты, услуги и подключения. API: `/api/v1/gpon/`.
- `apps/maps/` — карты и слои, включая защищённую отдачу файлов. API: `/api/v1/maps/`.
- `apps/net_tools/` — поиск по описаниям, MAC/IP, VLAN traceroute и топология. API: `/api/v1/tools/`.
- `apps/notifications/` — webhook/Telegram-уведомления, триггеры, условия и Celery-задачи.
- `apps/ring_manager/` — транспортные и access-кольца. API: `/api/v1/ring-manager/`.
- `apps/news/` — глобальные новости приложения. Модель: `GlobalNews`.

Типовая структура приложения:

- `models.py` — модели.
- `api/urls.py`, `api/views/`, `api/serializers.py` — DRF API.
- `services/` — бизнес-логика, которую не следует переносить во views/serializers.
- `tasks.py` — Celery-задачи.
- `tests/` — Django-тесты.
- `migrations/` — миграции; при изменении моделей обязательно проверять их состояние.

## Devicemanager

- `devicemanager/dc.py` и `devicemanager/device/` — фабрики и высокоуровневое API устройств.
- `devicemanager/remote/` — HTTP-клиент отдельного device-connector.
- `devicemanager/device_connector/` — создание сессий, пулы и статусы подключений.
- `devicemanager/session_control.py` — жизненный цикл и переиспользование сессий.
- `devicemanager/vendors/` — реализации оборудования разных производителей.
- `devicemanager/templates/` — TextFSM-шаблоны интерфейсов, VLAN и ARP.
- `devicemanager/tests/` — тесты драйверов, фабрик, сессий и connector API.

Изменения в общем API базового устройства или фабрик имеют большой радиус влияния: проверять связанные vendor-классы и `devicemanager/tests/`. Тесты не должны устанавливать реальные соединения с оборудованием; использовать mock/fixture-подход существующих тестов.

## Frontend

- `frontend_v/src/pages/` — страницы по функциональным областям.
- `frontend_v/src/components/` — переиспользуемые компоненты.
- `frontend_v/src/services/` — запросы к backend и клиентские сервисы.
- `frontend_v/src/store/` — Vuex store, включая авторизацию.
- `frontend_v/src/types/` — общие TypeScript-типы.
- `frontend_v/src/assets/base.css` и `frontend_v/src/style.css` — глобальные стили.
- Alias `@` указывает на `frontend_v/src`.
- Приложение использует JWT; Keycloak/OIDC включается конфигурацией backend.

Форматирование frontend задаёт `.prettierrc.json`: 4 пробела, двойные кавычки, `printWidth=120`, CRLF. Следовать существующему стилю Vue-компонентов и не включать отключённые ESLint-правила без отдельной задачи.

Для arbitrary values Tailwind колонки `grid-template-columns` разделяются пробелами, которые записываются через `_`, а не запятыми:

- Неверно: `lg:grid-cols-[1fr,16rem,16rem,auto]`.
- Верно: `lg:grid-cols-[1fr_16rem_16rem_auto]`.
- Запятые внутри `minmax(...)` допустимы: `grid-cols-[minmax(0,14rem)_minmax(0,1fr)]`.

## API и авторизация

- Основной API версионирован префиксом `/api/v1/`.
- По умолчанию DRF требует `IsAuthenticated`.
- Поддерживаются JWT Bearer, `UserAPIToken` и Django session authentication.
- JWT endpoints: `/api/token`, `/api/token/refresh`, `/api/token/verify`.
- Swagger: `/api/swagger/`; Redoc: `/api/redoc/`.
- Keycloak/OIDC опционален и включается через `KEYCLOAK_ENABLE`.
- Ошибки API проходят через `ecstasy_project.error_handler.custom_exception_handler`; сохранять существующий формат ошибок.

## Команды

Установка backend-зависимостей:

```powershell
uv sync --locked --all-extras --dev
```

Проверки backend:

```powershell
uv run mypy .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py test
```

Точечные тесты:

```powershell
uv run python manage.py test apps.check.tests
uv run python manage.py test devicemanager.tests
```

### Важно

Не запускать: `black`, `ruff` и `mypy` самостоятельно, только если явно было указано.

Не запускать `prettier`, также:

```powershell
npm run dev
npm run lint
npm run format:check
npm run check
```

Все проверки, линтеры и форматирование будут запущены вручную в отдельное время.

## Docker:

```powershell
docker compose build
docker compose up -d
```

## Соглашения backend

- Использовать PEP 8 и настройки форматирования из `pyproject.toml`.
- Все функции должны иметь docstring.
- Для backend писать тесты на базе Django test framework.
- Для исправления бага сначала добавить или определить тест, воспроизводящий проблему.
- При изменении моделей создавать миграцию и запускать `makemigrations --check --dry-run`.
- Сохранять разделение слоёв: API-код в `api/`, бизнес-логика в `services/`, работа с оборудованием в `devicemanager/`.
- Не выполнять сетевые вызовы, Celery-задачи или обращения к внешним Zabbix/Keycloak/Telegram API в unit-тестах без моков.

## Проверка перед завершением

- Backend-изменение: целевые тесты плюс `uv run python manage.py check`.
- Изменение моделей: миграции плюс `makemigrations --check --dry-run`.
- Изменение общего `devicemanager`: соответствующие тесты в `devicemanager/tests/`.
- Frontend-изменение: `npm run lint`, `npm run format:check`, `npm run build`.
- Изменение сквозного пользовательского сценария: проверить согласованность frontend service, Django URL/view/serializer и permissions.
