### CI/CD, Jenkins

Чтобы автоматизировать процесс развертывания приложения, можно использовать
Jenkins вместе с Ansible.

![img.png](../img/jenkins-ansible.png)

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
