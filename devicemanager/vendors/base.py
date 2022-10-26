import re
import pathlib
import pexpect
from abc import ABC, abstractmethod

# Папка с шаблонами регулярных выражений для парсинга вывода оборудования
TEMPLATE_FOLDER = pathlib.Path(__file__).parent.parent / 'templates'

# Обозначения медных типов по стандарту IEEE 802.3
COOPER_TYPES = [
    'T', 'TX', 'VG', 'CX', 'CR'
]

# Обозначения оптических типов по стандарту IEEE 802.3
FIBER_TYPES = [
    'FOIRL', 'F', 'FX', 'SX', 'LX', 'BX', 'EX', 'ZX', 'SR', 'ER', 'SW', 'LW', 'EW', 'LRM', 'PR', 'LR', 'ER', 'FR'
]


def _interface_normal_view(interface) -> str:
    """
    Приводит имя интерфейса к виду принятому по умолчанию для коммутаторов

    Например:

    >>> _interface_normal_view("Eth 0/1")
    'Ethernet 0/1'

    >>> _interface_normal_view("GE1/0/12")
    'GigabitEthernet 1/0/12'
    """

    interface_number = re.findall(r'(\d+([/\\]?\d*)*)', str(interface))
    if re.match(r'^[Ee]t', interface):
        return f"Ethernet {interface_number[0][0]}"
    elif re.match(r'^[Ff]a', interface):
        return f"FastEthernet {interface_number[0][0]}"
    elif re.match(r'^[Gg][ieE]', interface):
        return f"GigabitEthernet {interface_number[0][0]}"
    elif re.match(r'^\d+', interface):
        return re.findall(r'^\d+', interface)[0]
    elif re.match(r'^[Tt]e', interface):
        return f'TenGigabitEthernet {interface_number[0][0]}'
    else:
        return ''


def _range_to_numbers(ports_string: str) -> list:
    """
    Переводит строку с диапазоном чисел в список

    Например:

    >>> _range_to_numbers("10 to 14")
    [10, 11, 12, 13, 14]

    >>> _range_to_numbers("134-136, 234, 411")
    [134, 135, 136, 234, 411]
    """

    ports_split = []
    if 'to' in ports_string:
        # Если имеется формат "trunk,1 to 7 12 to 44"
        vv = [list(range(int(v[0]), int(v[1]) + 1)) for v in
              [range_ for range_ in re.findall(r'(\d+)\s*to\s*(\d+)', ports_string)]]
        for v in vv:
            ports_split += v
        return sorted(ports_split)
    elif ',' in ports_string:
        ports_split = ports_string.replace(' ', '').split(',')
    else:
        ports_split = ports_string.split()

    res_ports = []
    for p in ports_split:
        try:
            if '-' in p:
                port_range = list(range(int(p.split('-')[0]), int(p.split('-')[1]) + 1))
                for pr in port_range:
                    res_ports.append(int(pr))
            else:
                res_ports.append(int(p))
        except:
            pass

    return sorted(res_ports)


class BaseDevice(ABC):
    """
    Базовый класс для устройств, содержит обязательные методы и начальные параметры для выполнения удаленных команд
    """

    prompt: str  # Регулярное выражение, которое указывает на приглашение для ввода следующей команды

    # Регулярное выражение, которое указывает на ожидание ввода клавиши, для последующего отображения информации
    space_prompt: str
    mac_format = ''  # Регулярное выражение, которое определяет отображение МАС адреса
    SAVED_OK = 'Saved OK'  # Конфигурация была сохранена
    SAVED_ERR = 'Saved Error'  # Ошибка при сохранении конфигурации
    vendor: str

    def __init__(self, session: pexpect, ip: str, auth: dict, model: str = ''):
        self.session: pexpect.spawn = session
        self.ip = ip
        self.model: str = model
        self.auth: dict = auth
        self.mac: str = ''
        self.serialno: str = ''
        self.os: str = ''
        self.os_version: str = ''

    @staticmethod
    def clear_description(desc: str):
        """ Очищаем описание порта от лишних символов """

        desc = desc.strip().replace(' ', '_')
        desc = re.sub(r'\s', '', desc)
        desc = desc.replace('\\', '/')
        return desc[:220]

    @staticmethod
    def find_or_empty(pattern, string, *args, **kwargs):
        """ Используя pattern ищет в строке совпадения, если нет, то возвращает пустую строку """

        m = re.findall(pattern, string, *args, **kwargs)
        if m:
            return m[0]
        else:
            return ''

    def send_command(self, command: str, before_catch: str = None, expect_command=True, num_of_expect=10,
                     space_prompt=None, prompt=None, pages_limit=None) -> str:
        """
        Отправляет команду на оборудование и считывает её вывод

        Вывод будет содержать в себе строки от момента ввода команды, до (prompt: str), указанного в классе

        :param command: Команда, которую необходимо выполнить на оборудовании
        :param before_catch: Регулярное выражение, указывающее начало
        :param expect_command: Не вносить текст команды в вывод
        :param num_of_expect: Кол-во символов с конца команды, по которым необходимо её находить
        :param space_prompt: Регулярное выражение, которое указывает на ожидание ввода клавиши,
                             для последующего отображения информации
        :param prompt: Регулярное выражение, которое указывает на приглашение для ввода следующей команды
        :param pages_limit: Кол-во страниц, если надо, которые будут выведены при постраничном отображении
        :return: Строка с результатом команды
        """

        if space_prompt is None:
            space_prompt = self.space_prompt
        if prompt is None:
            prompt = self.prompt

        output = ''
        self.session.sendline(command)  # Отправляем команду

        if expect_command:
            self.session.expect(command[-num_of_expect:])  # Считываем введенную команду с поправкой по длине символов
        if before_catch:
            self.session.expect(before_catch)

        if space_prompt:  # Если необходимо постранично считать данные, то создаем цикл
            while pages_limit is None or pages_limit > 0:
                match = self.session.expect(
                    [
                        prompt,  # 0 - конец
                        space_prompt,  # 1 - далее
                        pexpect.TIMEOUT  # 2
                    ],
                    timeout=20
                )
                output += self.session.before.decode(errors='ignore')  # Убираем лишние символы
                output = output.replace('[42D                                          [42D', '')
                if match == 0:
                    break
                elif match == 1:
                    self.session.send(" ")  # Отправляем символ пробела, для дальнейшего вывода
                    output += '\n'
                else:
                    print(f'{self.ip} - timeout во время выполнения команды "{command}"')
                    break

                # Если задано кол-во страниц
                if pages_limit:
                    pages_limit -= 1

        else:  # Если вывод команды выдается полностью, то пропускаем цикл
            try:
                self.session.expect(prompt)
            except pexpect.TIMEOUT:
                pass
            output = self.session.before.decode('utf-8')
        return output

    @abstractmethod
    def get_interfaces(self) -> list:
        """
        Интерфейсы на оборудовании

        :return: [ ['name', 'status', 'desc'], ... ]
        """

    @abstractmethod
    def get_vlans(self) -> list:
        """
        Интерфейсы и VLAN на оборудовании

        :return: [ ['name', 'status', 'desc', 'vlans'], ... ]
        """

    @abstractmethod
    def get_mac(self, port: str) -> list:
        """
        Поиск маков на порту

        :return: [ ('vid', 'mac'), ... ]
        """

    @abstractmethod
    def reload_port(self, port: str, save_config=True) -> str:
        """Перезагрузка порта"""

    @abstractmethod
    def set_port(self, port: str, status: str, save_config=True) -> str:
        """Изменение состояния порта"""

    @abstractmethod
    def save_config(self):
        """ Сохраняем конфигурацию оборудования """

    @abstractmethod
    def set_description(self, port: str, desc: str) -> str:
        """ Изменяем описание порта """

