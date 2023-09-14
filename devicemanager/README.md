
# Модуль для работы с оборудованием


Отвечает за подключение к оборудованию разных вендоров.


## Подключение к оборудованию

Для подключения необходимо передать:
- IP адрес;
- протокол подключения (доступны `ssh` или `telnet`);
- объект для авторизации (любой объект у которого имеются атрибуты `login`, `password`, `secret`).

```python
from devicemanager.dc import DeviceRemoteConnector, SimpleAuthObject
from devicemanager.vendors.cisco import Cisco

# Создаем базовый объект авторизации к оборудованию.
# Логин, пароль, пароль от привилегированного режима.
auth = SimpleAuthObject("login", "password", "secret")

# Подключаемся с помощью контекстного менеджера подключение.
with DeviceRemoteConnector(ip="10.10.10.10", protocol="ssh", auth_obj=auth) as conn:
    # В зависимостри от вендора оборудования при подключении класс возвращаемого
    # объекта будет вычислен автоматически.
    print(conn.__class__ == Cisco)  # True.

    # Можно выполнять удаленные команды
    version = conn.send_command("show version")

    # Получать данные по интерфейсам
    interfaces = conn.get_interfaces()

    # Изменять состояние портов и т.д.
    conn.set_port("gi1/0/1", "up")
```

## Глобальная сессия

После подключения к оборудованию сессия удаленного подключения будет активна ещё `2 минуты`. Таким образом при выполнении кода

```python
with DeviceRemoteConnector(ip="10.10.10.10", protocol="ssh", auth_obj=auth) as conn:
	interfaces = conn.get_interfaces()
```

нового подключения к оборудованию не произойдет, а будет использована сессия, которая была создана ранее.

> Сессия будет доступна 2 минуты, после повторной инициализации `DeviceFactory` таймаут сессии будет сбрасываться снова до 2х минут.

Для каждого IP адреса будет храниться своя сессия, получить её можно через объект  `DEVICE_SESSIONS`.

```python
from devicemanager.session_control import DEVICE_SESSIONS
from devicemanager.vendors.cisco import Cisco


# Проверка существования доступной сессии
print(DEVICE_SESSIONS.has_connection("10.10.10.10"))  # True

# Получение сессии
connection = DEVICE_SESSIONS.get_connection("10.10.10.10")

print(connection.__class__ == Cisco)  # True

# Получение интерфейсов
interfaces = connection.get_interfaces()
```

За автоматическое очищение сессий отвечает метод `run_session_cleaner` объекта `DEVICE_SESSIONS`, который запускается автоматически при импорте. Он создает поток, в котором циклически просматриваются все сессии с периодом 30 секунд и закрываются истекшие.

> В рамках глобальной сессии одновременное выполнение команд на оборудовании невозможно, так как удаленный терминал только один.

## Без глобальной сессии

Чтобы подключиться к оборудованию без создания сессии и минуя существующую необходимо указать дополнительный параметр:

```python
with DeviceRemoteConnector(ip="10.10.10.10", protocol="ssh", auth_obj=auth, make_session_global=False) as conn:
	interfaces = conn.get_interfaces()
```
