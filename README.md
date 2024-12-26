# Ecstasy

![Python](https://img.shields.io/badge/python-3.10-blue.svg)
[![Code style: black](https://img.shields.io/badge/code_style-black-black.svg)](https://github.com/psf/black)

<div> 
<img src="https://www.vectorlogo.zone/logos/nginx/nginx-icon.svg" alt="nginx" width="30" height="30"/>
<img src="https://www.vectorlogo.zone/logos/vuejs/vuejs-icon.svg" alt="vue.js" width="30" height="30"/>
<img src="https://cdn.worldvectorlogo.com/logos/django.svg" alt="django" width="30" height="30"/>
<img src="https://havola.uz/uploads/logos/90/sb4u0gqv.png" alt="celery" width="30" height="30"/>
<img src="https://www.vectorlogo.zone/logos/redis/redis-icon.svg" alt="redis" width="32" height="32"/>
<img src="https://www.vectorlogo.zone/logos/mysql/mysql-icon.svg" alt="mysql" width="32" height="32"/>
<img src="https://www.vectorlogo.zone/logos/ansible/ansible-icon.svg" alt="ansible" width="32" height="32"/>
<img src="https://www.vectorlogo.zone/logos/jenkins/jenkins-icon.svg" alt="jenkins" width="32" height="32"/>
</div>

### Веб-приложение для взаимодействия с сетевым оборудованием

Позволяет отображать информацию о сетевых устройствах в удобном для чтения формате
без ввода консольных команд.

![img.png](img/img_3.png)

### Структура

![img.png](img/img_8.png)

Web-console позволит подключаться к оборудованию через терминал в браузере

Чтобы запустить и настроить web-console нужно [следовать инструкции](web-console/README.md).

### Возможности:

- Взаимодействие с сетевым оборудованием
    - Отображение интерфейсов оборудования в реальном времени
    - Управление состоянием порта (up/down)
    - Просмотр MAC адресов на порту
    - Просмотр текущей конфигурации порта
    - Перенаправление для просмотра логов в Elastic Stack
    - Просмотр ошибок на порту
    - Возможность просматривать и сбрасывать текущую сессию по MAC адресу
    - Сохранение файлов конфигураций оборудования

Кроме того, Ecstasy предоставляет дополнительные функции для визуализации
и поиска сетевой информации:

- Отображение топологии VLAN / MAC
- Поиск по текстовому описанию интерфейсов
- Поиск IP/MAC адреса
- Создание и просмотр интерактивных карт

### Поддержка производителей оборудования:

Список поддерживаемых вендоров приведен ниже. Другие модели тоже могут быть совместимы, но я имею доступ только к этим
устройствам.

- `Cisco`
    - Проверено для: `WS-C4500*` `WS-C35*0` `WS-C3750*` `ME-3*00X` `ME-4924` `ME-3400`
- `Eltex`
    - Проверено для: `MES3324*` `ESR-12VF` `LTP-4X(8X)-rev.*` `LTP-16N`
- `MikroTik`
    - Проверено для: `RouterOS v6.* (v7.*)`
- `Huawei`
    - Проверено для: `S2403TP` `S2326TP` `CX600-X8` `CE6865`
- `Huawei DSL (GPON)`
    - Проверено для: `MA5600T`
- `Iskratel DSL`
    - Проверено для: `MPC8560`
- `D-Link`
    - Проверено для: `DES-3200-*` `DES-3028` `DES-3526` `DGS-3420` `DGS-12**`
- `Extreme`
    - Проверено для: `X460-*` `X670-*`
- `ZTE`
    - Проверено для: `ZXR10 2928E` `2936-FI` `2952E`
- `Q-Tech`
    - Проверено для: `QSW-3450-*` `QSW-8200-*`

## Запуск

### Docker

Рекомендуемым и простым способом является запуск через docker compose.

Для начала скопируйте файл `.env.example` в `.env` и укажите свои данные в нём.

```shell
cp .env.example .env
```

Теперь запустите контейнеры.

```shell
docker compose build;
docker compose up -d;
```

По умолчанию создастся пользователь: `admin/password1`.

### CI/CD, Jenkins

Чтобы автоматизировать процесс развертывания приложения, можно использовать
Jenkins вместе с Ansible.

![img.png](img/jenkins-ansible.png)

### Запуск через Ansible

1. Копируем проект и переходим в папку `ansible`.
2. Прописываем в файле `inventory/hosts` IP адрес и порт для подключения сервера, на который будет установлена система.
3. В папке `roles` находятся файлы с параметрами настройки приложения:

- `ecstasy-main.yaml` содержит основные переменные проекта;

```yaml
# ------- DIRS --------
root_folder: "/home/ecstasy" # Директория проекта

# ------ PYTHON -------
python_version: 3.11

# -------- WEB --------
django_superuser_username: superusername
django_superuser_password: password

gunicorn_socket: 127.0.0.1:8000
device_connector_socket: 127.0.0.1:9999

celery_concurrent: 2
celery_worker_name: worker1

flower_address: 0.0.0.0
flower_port: 5555
flower_username: monitoring
flower_password: flower-password

nginx_http_listen_port: 80
enable_https: no
# При включении HTTPS будет создан самоподписанный сертификат

# ------- REDIS --------
redis_broker_db: 0
redis_cache_db: 1
redis_password: redis-password
```

- `ecstasy-mariadb.yaml` - параметры для базы данных;

```yaml
mysql_root_password: root-password

# Пользователь будет создан
mariadb_user: ecstasy
mariadb_password: ecstasy-password
# База будет создана
mariadb_database: ecstasy

```

- `ecstasy-services.yaml` - для работы сервисов.

```yaml
# Названия сервисов
ECSTASY_SERVICE_NAME: ecstasy
CELERY_SERVICE_NAME: ecstasy-celery
DEVICE_CONNECTOR_SERVICE_NAME: ecstasy-device-connector
FLOWER_SERVICE_NAME: ecstasy-flower

# Переменные окружения для сервисов Ecstasy.
ALLOWED_HOSTS: "*"
DJANGO_DEBUG: 0
CONFIG_STORAGE_DIR: # директория в которую будут сохраняться файлы конфигураций 
DJANGO_SECRET_KEY:
CONTACT_NAME: # имя для обратной связи
CONTACT_EMAIL: # почта обратной связи
CACHE_KEY_PREFIX: ecstasy_prod
DEVICE_CONNECTOR_TOKEN: # токен для защиты device connector
DEVICE_CONNECTOR_DEFAULT_POOL_SIZE: 2 # кол-во сессий по умолчанию для одного сетевого оборудования
```

Необходимо указать недостающие и/или поменять параметры по умолчанию.

5. Далее запускаем ansible:

```shell
ansible-playbook -K -i inventory/hosts playbooks/deploy-ecstasy.yaml
```

6. Вводим пароль суперпользователя и ожидаем завершение установки.

---

### Удобный поиск оборудования

![img.png](img/img_4.png)

### Просмотр загруженности интерфейсов оборудований

![img.png](img/img_9.png)

При выборе оборудования показывается его информация:

- Состояние оборудования
- Нагрузка CPU, RAM, Flash и температура
- Подробная информация (берется из Zabbix)
- Ссылка в Zabbix
- Ссылка на карту с местоположением оборудования
- Логи в Elastic Search
- Перечень конфигураций
- Медиафайлы
- Интерфейсы

![img.png](img/img.png)

При выборе конкретного порта открывается его информация:
Описание, конфигурация, счетчик ошибок, диагностика состояния кабеля, список VAC адресов

![img_1.png](img/img_1.png)

Для станционных терминалов GPON OLT возможен следующий вывод информации об интерфейсе (указан ниже)

![img.png](img/img_2.png)

## Карты

Реализована возможность отображать и создавать интерактивные карты:

- Из ссылки на внешнюю карту;
- Из HTML файла карты;
- Из совокупности различных слоев. Слой может быть представлен:
    - Из группы в Zabbix (будут отображаться узлы сети, которые имеют координаты);
    - Из файла формата GEOJSON.

Интерактивные карты со слоями из Zabbix группы отображают доступность оборудования
с описанием проблемы в Zabbix.

![img.png](img/interactive-map.png)

## Топология VLAN

Построение топологии VLAN по оборудованию.

![img.png](img/img_6.png)

## Топология прохождения MAC адреса

Определение маршрута MAC адреса между оборудованиями.

![img.png](img/img_10.png)

## Поиск по описанию порта

![img.png](img/img_5.png)

### Поиск IP или MAC адреса

![img.png](img/img_7.png)

## Кастомные команды

### import_from_zabbix

    # python manage.py import_from_zabbix

    Импорт узлов сети из zabbix
    
    options:
      -h, --help            show this help message and exit
      -g GROUPS, --groups GROUPS
                            Имена Zabbix групп через запятую
      -a AUTH, --auth AUTH  Имя группы авторизации для узла сети
      -s, --save            Сохранить в базу узлы сети
      --change-group CHANGE_GROUP
                            Имя группы Ecstasy, которая будет использоваться для всех узлов сети. Если не указана, то будет использована оригинальная группа Zabbix
      --all-status          Импортируем также узлы сети, которые деактивированы в Zabbix
      --interface-scan {telnet,ssh,snmp}
                            Протокол для сбора интерфейсов узла сети. (по умолчанию ssh)
      --snmp-community SNMP_COMMUNITY
                            SNMP Community (необязательно)
      --cli-protocol {telnet,ssh}
                            Протокол для выполнения команд узла сети. (по умолчанию ssh)
      --name-pattern NAME_PATTERN
                            Паттерн для имени узлов сети. Если совпадает, то будет импортирован. (необязательно)
      --ip-pattern IP_PATTERN
                            Паттерн для IP узла сети. Если совпадает, то будет импортирован. (необязательно)
      --server SERVER       URL сервера Zabbix (необязательно)
      --user USER           Имя пользователя Zabbix (необязательно)
      --password PASSWORD   Пароль пользователя Zabbix (необязательно)
      --debug               Выводить дополнительную информацию
      --version             Show program's version number and exit.
      -v {0,1,2,3}, --verbosity {0,1,2,3}
                            Verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output
      --settings SETTINGS   The Python path to a settings module, e.g. "myproject.settings.main". If this isn't provided, the DJANGO_SETTINGS_MODULE environment variable will be used.
      --pythonpath PYTHONPATH
                            A directory to add to the Python path, e.g. "/home/djangoprojects/myproject".
      --traceback           Raise on CommandError exceptions.
      --no-color            Don't colorize the command output.
      --force-color         Force colorization of the command output.
      --skip-checks         Skip system checks.

> [!NOTE]
> По умолчанию используются данные авторизации Zabbix хранимые в базе.
> Указывается через панель администратора: `App settings -> Zabbix API settings`
> Чтобы не сохранять в базу данных, а только протестировать какие узлы будут учитываться
> нужно выполнять команды без параметра `--save`.

### Примеры:

Импорт активных узлов сети из Zabbix группы `devs` в новую группу `devs` ecstasy,
с указанием группы авторизации `creds-1`, а также использование `telnet`
как способа подключения к оборудованию:

```shell
python manage.py import_from_zabbix --save -g devs -a creds-1 --interface-scan=telnet --cli-protocol=telnet
```

---

Импорт активных узлов сети из диапазона `172.30.0.0/24` Zabbix группы `devs` в новую группу `devs` ecstasy,
с указанием группы авторизации `creds-1`, а также использование `ssh` (По умолчанию SSH)
как способа подключения к оборудованию:

```shell
python manage.py import_from_zabbix --save -g devs -a creds-1 --ip-pattern='172\.30\.0\.\d+'
```

## Создание связей моделей

```shell
python manage.py graph_models -a --rankdir LR --dot -g -o ./docs/models.dot
dot -Tsvg ./docs/models.dot -o ./docs/models.svg
```
