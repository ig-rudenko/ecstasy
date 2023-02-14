# Ecstasy

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
[![Code style: black](https://img.shields.io/badge/code_style-black-black.svg)](https://github.com/psf/black)

<div>
<img src="https://www.vectorlogo.zone/logos/vuejs/vuejs-icon.svg" alt="vue.js" width="30" height="30"/>
<strong style="padding: 2px; vertical-align: text-bottom">+</strong>
<img src="https://cdn.worldvectorlogo.com/logos/django.svg" alt="django" width="30" height="30"/>
<strong style="padding: 2px; vertical-align: text-bottom">+</strong>
<img src="https://www.vectorlogo.zone/logos/redis/redis-icon.svg" alt="redis" width="32" height="32"/>
<strong style="padding: 2px; vertical-align: text-bottom">+</strong>
<img src="https://codeguida.com/media/post_title/celery-logo.png" alt="celery" width="32" height="32"/>
</div>

### Веб-приложение для взаимодействия с сетевым оборудованием

Позволяет отображать информацию о сетевых устройствах в удобном для чтения формате
без ввода консольных команд.

![img.png](img/img_3.png)

### Возможности:

- Взаимодействие с сетевым оборудованием
  - Отображение интерфейсов оборудования в реальном времени
  - Управление состоянием порта (up/down)
  - Просмотр MAC адресов на порту
  - Просмотр текущей конфигурации порта
  - Перенаправление для просмотра логов в Elastic Stack
  - Просмотр ошибок на порту
  - Возможность просматривать и сбрасывать текущую сессию по MAC адресу


- Отображение топологии VLAN
- Поиск по текстовому описанию интерфейсов
- Поиск IP/MAC адреса
- Создание и просмотр интерактивных карт

### Поддержка производителей оборудования:

В данный момент поддерживаются следующие вендоры:
- Cisco
- Eltex
- Huawei
- Huawei DSL
- Huawei GPON
- Iskratel DSL
- D-Link
- Extreme
- ZTE
- Q-Tech
- Edge-Core

## Структура docker compose

![img.png](img/img_8.png)

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
- Интерфейсы


![img.png](img/img.png)


При определении MAC адресов на порту добавляется также другая полезная информация о нём

На изображении ниже представлен вывод состояния DSL порта, где также указываются
основные параметры линии помимо MAC адреса

![img_1.png](img/img_1.png)

Для другого оборудования возможен следующий вывод информации об интерфейсе (указан ниже)

Определяется тип порта (SFP или copper), можно посмотреть конфигурацию порта


![img.png](img/img_2.png)

## Дополнительные утилиты

### Поиск по описанию порта

![img.png](img/img_5.png)

### Посмотреть, как проходит VLAN по сети

![img.png](img/img_6.png)

### Поиск IP или MAC адреса

![img.png](img/img_7.png)
