import re
from time import sleep
from functools import lru_cache
import pexpect
import textfsm
from .base import BaseDevice, TEMPLATE_FOLDER, COOPER_TYPES, FIBER_TYPES, _range_to_numbers, \
    _interface_normal_view


class Huawei(BaseDevice):
    """
    Для оборудования от производителя Huawei

    Проверено для:
     - S2403TP
     - S2326TP
    """

    prompt = r'<\S+>$|\[\S+\]$|Unrecognized command'
    space_prompt = r"---- More ----"
    mac_format = r'\S\S\S\S-\S\S\S\S-\S\S\S\S'
    vendor = 'Huawei'

    def __init__(self, session: pexpect, ip: str, auth: dict, model=''):
        super().__init__(session, ip, auth, model)
        self.session.sendline('super')
        v = session.expect(
            [
                'Unrecognized command|Now user privilege is 3 level',  # 0 - huawei-2326
                '[Pp]ass',  # 1 - huawei-2403 повышение уровня привилегий
                'User privilege level is'  # 2 - huawei-2403 уже привилегированный
            ]
        )
        if v == 1:
            self.session.sendline(self.auth['privilege_mode_password'])

        if self.session.expect(
                [
                    r'<\S+>',  # 0 - режим просмотра
                    r'\[\S+\]'  # 1 - режим редактирования
                ]
        ):  # Если находимся в режиме редактирования, то понижаем до режима просмотра
            self.session.sendline('quit')
            self.session.expect(r'<\S+>$')

        version = self.send_command('display version')
        self.model = self.find_or_empty(r'Quidway (\S+) [Routing Switch]*uptime', version)

        if 'S2403' in self.model:
            manuinfo = self.send_command('display device manuinfo')
            self.mac = self.find_or_empty(r'MAC ADDRESS\s+:\s+(\S+)', manuinfo)
            self.serialno = self.find_or_empty(r'DEVICE SERIAL NUMBER\s+:\s+(\S+)', manuinfo)

        elif 'S2326' in self.model:
            mac = self.send_command('display bridge mac-address')
            self.mac = self.find_or_empty(r'System Bridge Mac Address\s+:\s+(\S+)\.', mac)

            elabel = self.send_command('display elabel')
            self.serialno = self.find_or_empty(r'BarCode=(\S+)', elabel)

    def save_config(self):
        self.session.sendline('save')
        self.session.expect(r'[Aa]re you sure.*\[Y\/N\]')
        self.session.sendline('Y')
        self.session.sendline('\n')
        if self.session.expect([self.prompt, r'successfully'], timeout=20):
            return self.SAVED_OK
        return self.SAVED_ERR

    def get_interfaces(self):
        output = ''
        if 'S2403' in self.model:
            ht = 'huawei-2403'
            output = self.send_command('display brief interface')
        elif 'S2326' in self.model:
            ht = 'huawei-2326'
            output = self.send_command('display interface description')
        else:
            ht = 'huawei'

        with open(f'{TEMPLATE_FOLDER}/interfaces/{ht}.template', 'r') as template_file:
            int_des_ = textfsm.TextFSM(template_file)
            result = int_des_.ParseText(output)  # Ищем интерфейсы
        return [
            [
                line[0],  # interface
                line[1].lower().replace('adm', 'admin').replace('*', 'admin '),  # status
                line[2]  # desc
            ]
            for line in result if not line[0].startswith('NULL') and not line[0].startswith('V')
        ]

    def get_vlans(self) -> list:
        interfaces = self.get_interfaces()
        result = []
        for line in interfaces:
            if not line[0].startswith('V') and not line[0].startswith('NU') and not line[0].startswith('A'):
                output = self.send_command(
                    f"display current-configuration interface {_interface_normal_view(line[0])}",
                    expect_command=False
                )

                vlans_group = re.sub(r'(?<=undo).+vlan (.+)', '', output)  # Убираем строчки, где есть "undo"
                vlans_group = list(set(re.findall(r'vlan (.+)', vlans_group)))  # Ищем строчки вланов, без повторений
                port_vlans = []
                for v in vlans_group:
                    port_vlans = _range_to_numbers(v)
                result.append(line + [port_vlans])

        return result

    def get_mac(self, port) -> list:
        """
        Поиск маков на порту
        :param port:
        :return: [ ('vid', 'mac'), ... ]
        """

        mac_list = []

        if '2403' in self.model:
            mac_str = self.send_command(f'display mac-address interface {_interface_normal_view(port)}')
            for i in re.findall(rf'({self.mac_format})\s+(\d+)\s+\S+\s+\S+\s+\S+', mac_str):
                mac_list.append(i[::-1])

        elif '2326' in self.model:
            mac_str = self.send_command(f'display mac-address {_interface_normal_view(port)}')
            for i in re.findall(rf'({self.mac_format})\s+(\d+)/\S+\s+\S+\s+\S+', mac_str):
                mac_list.append(i[::-1])

        return mac_list

    @lru_cache
    def __port_info(self, port):
        return self.send_command(f'display interface {_interface_normal_view(port)}')

    def port_type(self, port) -> str:
        res = self.__port_info(port)

        type_ = self.find_or_empty(r'Port hardware type is (\S+)|Port Mode: (.*)', res)
        print(f'{type_=}')
        if type_:

            type_ = type_[0] if type_[0] else type_[1]

            if "COMBO" in type_:
                return 'COMBO-' + self.find_or_empty(r'Current Work Mode: (\S+)', res)

            elif "FIBER" in type_ or 'SFP' in type_:
                return 'SFP'

            elif "COPPER" in type_:
                return 'COPPER'

            else:
                sub_type = self.find_or_empty(r'\d+_BASE_(\S+)', type_)
                if sub_type in COOPER_TYPES:
                    return 'COPPER'
                elif sub_type in FIBER_TYPES:
                    return 'FIBER'
                else:
                    return ''
        else:
            return ''

    def get_port_errors(self, port):
        return self.__port_info(port)

    def reload_port(self, port) -> str:
        self.session.sendline('system-view')
        self.session.sendline(f'interface {_interface_normal_view(port)}')
        self.session.sendline('shutdown')
        sleep(1)
        self.session.sendline('undo shutdown')
        self.session.sendline('quit')
        self.session.expect(r'\[\S+\]')
        self.session.sendline('quit')
        self.session.expect(r'\[\S+\]')
        r = self.session.before.decode(errors='ignore')
        s = self.save_config()
        return r + s

    def set_port(self, port, status) -> str:
        self.session.sendline('system-view')
        self.session.sendline(f'interface {_interface_normal_view(port)}')
        if status == 'up':
            self.session.sendline('undo shutdown')
        elif status == 'down':
            self.session.sendline('shutdown')
        self.session.expect(r'\[\S+\]')
        self.session.sendline('quit')
        self.session.expect(r'\[\S+\]')
        self.session.sendline('quit')
        self.session.expect(r'\[\S+\]')
        r = self.session.before.decode(errors='ignore')
        s = self.save_config()
        return r + s

    def port_config(self, port):
        config = self.send_command(
            f'display current-configuration interface {_interface_normal_view(port)}',
            expect_command=False, before_catch=r'#'
        )
        return config

    def set_description(self, port: str, desc: str) -> str:
        self.session.sendline('system-view')
        self.session.sendline(f'interface {_interface_normal_view(port)}')

        desc = self.clear_description(desc)  # Очищаем описание от лишних символов

        if desc == '':  # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            status = self.send_command(f'undo description', expect_command=False)

        else:  # В другом случае, меняем описание на оборудовании
            status = self.send_command(f'description {desc}', expect_command=False)

        if 'Wrong parameter found' in status:
            # Если длина описания больше чем доступно на оборудовании
            output = self.send_command('description ?')
            return 'Max length:' + self.find_or_empty(r'no more than (\d+) characters', output)

        self.session.sendline('quit')
        self.session.sendline('quit')


class HuaweiMA5600T(BaseDevice):
    """
    Для оборудования DSLAM MA5600T от производителя Huawei
    """

    prompt = r'config\S+#|\S+#'
    space_prompt = r'---- More \( Press \'Q\' to break \) ----'
    mac_format = r'\S\S\S\S-\S\S\S\S-\S\S\S\S'
    vendor = 'Huawei'

    def __init__(self, session: pexpect, ip: str, auth: dict, model=''):
        super().__init__(session, ip, auth, model)
        self.session.sendline('enable')
        self.session.expect(r'\S+#')

    def save_config(self):
        pass

    def split_port(self, port: str) -> tuple:
        """
        Разделяет строку порта на тип интерфейса и плата, слот, порт

        ADSL 0/2/4 -> "adsl", ["0", "2", "4"]

        Смотрит платы

            # display board

            #-------------------------------------------------------------------------
            SlotID  BoardName  Status         SubType0 SubType1    Online/Offline
            #-------------------------------------------------------------------------
            0
            1
            2       H808ADLF   Normal
            3       H808ADLF   Normal
            4       H808ADLF   Normal
            5       H808ADLF   Normal
            6       H808ADLF   Normal
            7
            8       H805ADPD   Normal
            9       H801SCUB   Active_normal


        ethernet0/9/2 -> "scu", ["0", "9", "2"]

        """

        port = port.lower().strip()
        type_ = self.find_or_empty(r'^ethernet|^adsl|^gpon', port)
        indexes = re.sub(r'^[a-z]+', '', port).split('/')
        if type_ == 'ethernet':
            board_info = self.send_command(f'display board {indexes[0]}')
            print(board_info)
            board_list = self.find_or_empty(rf'\s+({indexes[1]})\s+(\S+)\s+\S+', board_info)
            if board_list:
                if 'SCU' in board_list[1]:
                    return 'scu', indexes
                elif 'GI' in board_list[1]:
                    return 'giu', indexes

            return 'eth', indexes

        return type_, indexes

    def port_info_parser(self, info: str):
        """
        Преобразовываем информацию о порте для отображения на странице
        """

        def color(val: float, s: str) -> str:
            """ Определяем цвета в зависимости от числовых значений показателя """
            if 'channel SNR margin' in s:
                gradient = [5, 7, 10, 20]
            elif 'channel attenuation' in s:
                gradient = [-60, -50, -40, -20]
                val = -val
            elif 'total output power' in s:
                return '#95e522' if val >= 10 else '#e5a522'
            else:
                return ''
            # проверяем значения по градиенту
            if val <= gradient[0]:
                return '#e55d22'
            if val <= gradient[1]:
                return '#e5a522'
            if val <= gradient[2]:
                return '#dde522'
            if val <= gradient[3]:
                return '#95e522'
            else:
                return '#22e536'

        lines = info.strip().split('\n')  # Построчно создаем список
        html = '<div class="row"><div class="col-4">'  # Создаем ряд и начало первой колонки
        table = """
            <div class="col-8">
                <table class="table">
                  <thead>
                    <tr>
                      <th></th>
                      <th scope="col" style="text-align: center;">Downstream</th>
                      <th scope="col" style="text-align: center;">Upstream</th>
                    </tr>
                  </thead>
                  <tbody>
                """
        table_dict = {
            'Do': [],
            'Up': []
        }
        for line in lines:  # Построчно смотрим данные
            line = line.strip()

            if line.startswith('-' * 10):  # Прерываем, если дошли до строки с разделителем ------------
                break

            if not re.findall(r'^[DU].+?(-?\d+\.?\d*)', line):
                html += f'<p>{line}</p>'  # Записываем в первую колонку данные
            else:
                value = self.find_or_empty(r'-?\d+\.?\d*', line)  # Числовое значение
                if value:
                    line_new = f'<td style="text-align: center; background-color: {color(float(value), line)};">{value}</td>'
                else:  # Если нет значения - ошибка
                    line_new = f'<td style="text-align: center; background-color: #e55d22;">0</td>'

                table_dict[line[:2]].append(line_new)  # Обновляем ключ Do или Up

        names = ['Фактическая скорость передачи данных (Кбит/с)', 'Максимальная скорость передачи данных (Кбит/с)',
                 'Сигнал/Шум (дБ)', 'Interleaved channel delay (ms)', 'Затухание линии (дБ)', 'Общая выходная мощность (dBm)']

        # Наполняем таблицу
        for line in zip(names, table_dict['Do'], table_dict['Up']):
            table += f"""
            <tr>
                <td style="text-align: right";>{line[0]}</td>
                {line[1]}
                {line[2]}
            </tr>
            """
        else:
            table += "</tbody></table></div>"  # Закрываем таблицу

        html += '</div>'  # Закрываем первую колонку
        html += table     # Добавляем вторую колонку - таблицу
        html += '</div>'  # Закрываем ряд
        return html

    def get_port_info(self, port: str):
        """Смотрим информацию на порту"""

        type_, indexes = self.split_port(port)

        if not type_ or len(indexes) != 3:
            return f'Неверный порт! ({port})'

        self.session.sendline('config')
        self.session.sendline(f'interface {type_} {indexes[0]}/{indexes[1]}')
        self.session.expect(r'\S+#')
        self.session.sendline(f'display line operation {indexes[2]}')
        if self.session.expect([r'Are you sure to continue', 'Unknown command']):
            return ''
        output = self.send_command('y', expect_command=True, before_catch=r'Failure|------[-]+')

        if 'is not activated' in output:  # У данного порта нет таких команд
            return ''

        profile_output = self.send_command(f'display port state {indexes[2]}')
        profile_index = self.find_or_empty(rf'\s+\d+\s+\S+\s+(\d+)', profile_output)
        profile_output = self.send_command(f'display adsl line-profile {profile_index}')
        profile_name = f'Profile name: <strong>' + self.find_or_empty(r"Name:\s+(\S+)", profile_output) + '</strong>\n'

        return self.port_info_parser(profile_name + output)

    def get_mac(self, port) -> list:
        """
        Смотрим MAC'и на порту и отдаем в виде списка

        [ ["vlan", "mac"],  ... ]
        """

        type_, indexes = self.split_port(port)

        if len(indexes) != 3:  # Неверный порт
            return []

        self.session.sendline(f'display mac-address port {"/".join(indexes)}')
        com = self.send_command('\n', expect_command=False, before_catch='display mac-address')
        macs1 = re.findall(rf'\s+\S+\s+\S+\s+\S+\s+({self.mac_format})\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+.+?\s+(\d+)', com)

        # Попробуем еще одну команду
        self.session.sendline(f'display security bind mac {"/".join(indexes)}')
        com = self.send_command('\n', expect_command=False, before_catch='display security')
        macs2 = re.findall(rf'\s+\S+\s+({self.mac_format})\s+\S+\s+\S+\s+\S+\s+\S+\s+(\d+)', com)

        res = []
        print(macs1+macs2)
        for m in macs1+macs2:
            res.append(m[::-1])
        return res

    @staticmethod
    def _up_down_command(port_type: str, status: str):
        """В зависимости от типа порта возвращает команды для управления его статусом"""
        if port_type == 'scu' or port_type == 'giu':
            if status == 'down':
                return 'shutdown'
            if status == 'up':
                return 'undo shutdown'

        if port_type == 'adsl':
            if status == 'down':
                return 'deactivate'
            if status == 'up':
                return 'activate'

    def reload_port(self, port) -> str:
        """Перезагружаем порт"""

        type_, indexes = self.split_port(port)
        if not type_ or len(indexes) != 3:
            return f'Неверный порт! ({port})'

        self.session.sendline('config')
        self.session.sendline(f'interface {type_} {indexes[0]}/{indexes[1]}')
        self.session.expect(r'\S+#')

        cmd = f"{self._up_down_command(type_, 'down')} {indexes[2]}"  # Выключить порт
        self.session.sendline(cmd)
        self.session.expect(cmd)
        self.session.sendline('\n')
        sleep(1)  # Пауза

        cmd = f"{self._up_down_command(type_, 'up')} {indexes[2]}"  # Включить порт
        self.session.sendline(cmd)
        self.session.expect(cmd)

        s = self.session.before.decode()

        self.session.sendline('\n')
        self.session.expect(r'\S+#$')

        s += self.session.before.decode()
        return s

    def set_port(self, port, status) -> str:
        type_, indexes = self.split_port(port)
        if not type_ or len(indexes) != 3:
            return f'Неверный порт! ({port})'

        self.session.sendline('config')
        self.session.sendline(f'interface {type_} {indexes[0]}/{indexes[1]}')
        self.session.expect(r'\S+#')

        # Выключаем или включаем порт, в зависимости от типа будут разные команды
        s = self.send_command(f'{self._up_down_command(type_, status)} {indexes[2]}', expect_command=False)
        self.send_command('\n', expect_command=False)

        return s

    def get_interfaces(self) -> list:
        pass

    def get_vlans(self) -> list:
        pass

    def set_description(self, port: str, desc: str) -> str:
        """ Меняем описание на порту """

        type_, indexes = self.split_port(port)
        if not type_ or len(indexes) != 3:
            return f'Неверный порт! ({port})'

        desc = self.clear_description(desc)

        if len(desc) > 32:
            # Длина описания не
            return 'Max length:32'

        self.session.sendline('config')

        if desc == '':  # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            self.session.sendline(f'undo port desc {indexes[0]}/{indexes[1]}/{indexes[2]}')

        else:  # В другом случае, меняем описание на оборудовании
            self.session.sendline(f'port desc {indexes[0]}/{indexes[1]}/{indexes[2]} description {desc}')

        self.session.sendline('quit')
        self.session.expect(self.prompt)


class HuaweiCX600(BaseDevice):
    prompt = r'<\S+>$|\[\S+\]$|Unrecognized command'
    space_prompt = r"  ---- More ----"
    mac_format = r'\S\S\S\S-\S\S\S\S-\S\S\S\S'
    vendor = 'Huawei'

    def search_mac(self, mac_address: str):
        formatted_mac = '{}{}{}{}-{}{}{}{}-{}{}{}{}'.format(*mac_address)

        match = self.send_command(
            f'display access-user mac-address {formatted_mac}',
            prompt=self.prompt + '|Are you sure to display some information',
            expect_command=False
        )
        self.session.sendline('N')
        # Форматируем вывод
        print(f'{TEMPLATE_FOLDER}/arp_format/{self.vendor.lower()}-{self.model.lower()}.template')
        with open(f'{TEMPLATE_FOLDER}/arp_format/{self.vendor.lower()}-{self.model.lower()}.template') as template_file:
            template = textfsm.TextFSM(template_file)
        formatted_result = template.ParseText(match)
        print(formatted_result)
        if formatted_result:
            return formatted_result[0]
        else:
            return []

    def get_interfaces(self) -> list:
        pass

    def get_vlans(self) -> list:
        pass

    def get_mac(self, port: str) -> list:
        pass

    def reload_port(self, port: str) -> str:
        pass

    def set_port(self, port: str, status: str) -> str:
        pass

    def save_config(self):
        pass

    def set_description(self, port: str, desc: str) -> str:
        pass
