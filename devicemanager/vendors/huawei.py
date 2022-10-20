import datetime
import re
import pexpect
import textfsm
from time import sleep
from functools import lru_cache
from django.template.loader import render_to_string
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

        return f'Description has been {"changed" if desc else "cleared"}.' + self.save_config()


class HuaweiMA5600T(BaseDevice):
    """
    Для оборудования MA5600T от производителя Huawei
    """

    prompt = r'config\S+#|\S+#'
    space_prompt = r'---- More \( Press \'Q\' to break \) ----'
    mac_format = r'\S\S\S\S-\S\S\S\S-\S\S\S\S'
    vendor = 'Huawei'

    def __init__(self, session: pexpect, ip: str, auth: dict, model=''):
        super().__init__(session, ip, auth, model)
        self.session.sendline('enable')
        self.session.expect(r'\S+#')

    def send_command(self, command: str, before_catch: str = None, expect_command=True, num_of_expect=10,
                     space_prompt=None, prompt=None, pages_limit=None) -> str:
        res = super(HuaweiMA5600T, self).send_command(
            command, before_catch, expect_command, num_of_expect, space_prompt, prompt, pages_limit
        )
        return res.replace('\n[37D                                     [37D', '')

    def save_config(self):
        pass

    def port_config(self, port: str):
        port_type, indexes = self.split_port(port)

        # Для GPON ONT используем отдельный поиск
        if port_type == 'gpon' and len(indexes) == 4:
            i: tuple = indexes
            self.session.sendline('config')
            self.session.expect(self.prompt)
            config = self.send_command(
                f'display current-configuration ont {i[0]}/{i[1]}/{i[2]} {i[3]}',
                prompt=r'\S+config\S+#',
                expect_command=False,
                before_catch=r'\[\S+: \S+\]'
            )
            self.session.sendline('quit')
            self.session.expect(self.prompt)
            return config.replace('<', '&#8249;').replace('>', '&#8250;')

        return ''

    def split_port(self, port: str) -> tuple:
        """
        Разделяет строку порта на тип интерфейса и плата, слот, порт

        ADSL 0/2/4 -> "adsl", ["0", "2", "4"]

        >>> self.split_port('ADSL 0/2/4')
        ('adsl', ['0', '2', '4'])

        >>> self.split_port('GPON 0/6/7/1')
        ('gpon', ['0', '6', '7', '1'])


        Также смотрит слоты

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

        Чтобы понять тип

        >>> self.split_port('ethernet0/9/2')
        ('scu', ['0', '9', '2'])


        """

        port = port.lower().strip()
        port_type = self.find_or_empty(r'^ethernet|^adsl|^gpon', port)
        indexes = re.sub(r'^[a-z]+', '', port).split('/')
        if port_type == 'ethernet':
            board_info = self.send_command(f'display board {indexes[0]}')
            # print(board_info)
            board_list = self.find_or_empty(rf'\s+({indexes[1]})\s+(\S+)\s+\S+', board_info)
            if board_list:
                if 'SCU' in board_list[1]:
                    return 'scu', indexes
                elif 'GI' in board_list[1]:
                    return 'giu', indexes

            return 'eth', indexes

        return port_type, tuple(indexes)

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

    def __get_gpon_port_info(self, indexes: tuple):
        """ Смотрим информацию на порту, который относится к GPON """

        from check.models import Devices

        # Проверяем индексы
        if not isinstance(indexes, tuple) or len(indexes) not in [3, 4]:
            return f'Неверный порт! (GPON {"/".join(indexes)})'

        self.session.sendline('config')  # Переходим в режим конфигурации
        self.session.expect(self.prompt)
        i: tuple = indexes  # Упрощаем запись переменной

        if len(indexes) == 3:
            # Смотрим порт
            output = self.send_command(
                f'display ont info summary {"/".join(i)}', before_catch='Please wait', expect_command=False
            )
            self.session.sendline('quit')

            data = {
                'device': Devices.objects.get(ip=self.ip).name,
                'port': f'GPON {"/".join(i)}',
                'total_count': self.find_or_empty(r'the total of ONTs are: (\d+), online: \d+', output),
                'online_count': self.find_or_empty(r'the total of ONTs are: \d+, online: (\d+)', output)
            }

            lines = re.findall(
                r'(\d+)\s+(online|offline)\s+(\d+-\d+-\d+ \d+:\d+:\d+)\s+(\d+-\d+-\d+ \d+:\d+:\d+)\s+(\S+)',
                output
            )

            ont_info = re.findall(
                r'\d+\s+\S+\s+\S+\s+([-\d]+)\s+(-?\d+\.?\d+/-?\d+\.?\d+|-/-)\s+\S+',
                output
            )

            data['onts_lines'] = []

            for j in range(len(lines)):
                part1 = list(lines[j])
                part2 = list(ont_info[j])

                part1[2] = datetime.datetime.strptime(part1[2], '%Y-%m-%d %H:%M:%S')
                part1[3] = datetime.datetime.strptime(part1[3], '%Y-%m-%d %H:%M:%S')

                data['onts_lines'].append(part1 + part2)

            return render_to_string('check/gpon_port_info.html', data)

        else:
            # Смотрим ONT
            data = self.__get_ont_port_info(indexes=i)
            self.session.sendline('quit')
            return render_to_string('check/ont_port_info.html', {'ont_info': data})

    @lru_cache
    def __get_ont_port_info(self, indexes: tuple):
        """
        Смотрим информацию на конкретном ONT

        display ont wan-info 0/1 1 11

        """
        i: tuple = indexes  # Упрощаем запись переменной
        info = self.send_command(f'display ont wan-info {i[0]}/{i[1]} {i[2]} {i[3]}', expect_command=False)
        data = []  # Общий список

        # Разделяем на сервисы
        parts = info.split('---------------------------------------------------------------')

        for service_part in parts:
            if 'Service type' not in service_part:
                # Пропускаем те части, которые не содержат информации о сервисе
                continue

            data.append({
                'type': self.find_or_empty(r'Service type\s+: (\S+)', service_part),
                'index': self.find_or_empty(r'Index\s+: (\d+)', service_part),
                'ipv4_status': self.find_or_empty(r'IPv4 Connection status\s+: (\S+)', service_part),
                'ipv4_access_type': self.find_or_empty(r'IPv4 access type\s+: (\S+)', service_part),
                'ipv4_address': self.find_or_empty(r'IPv4 address\s+: (\S+)', service_part),
                'subnet_mask': self.find_or_empty(r'Subnet mask\s+: (\S+)', service_part),
                'manage_vlan': self.find_or_empty(r'Manage VLAN\s+: (\d+)', service_part),
                'mac': self.find_or_empty(r'MAC address\s+: ([0-9A-F]+-[0-9A-F]+-[0-9A-F]+)', service_part)
            })

        return data

    def get_port_info(self, port: str):
        """ Смотрим информацию на порту """

        port_type, indexes = self.split_port(port)

        # Для GPON используем отдельный метод
        if port_type == 'gpon':
            return self.__get_gpon_port_info(indexes=indexes)

        # Для других
        if not port_type or len(indexes) != 3:
            return f'Неверный порт! ({port})'

        self.session.sendline('config')
        self.session.sendline(f'interface {port_type} {indexes[0]}/{indexes[1]}')
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
        self.session.sendline('quit')

        profile_name = f'Profile name: <strong>' + self.find_or_empty(r"Name:\s+(\S+)", profile_output) + '</strong>\n'

        return self.port_info_parser(profile_name + output)

    def get_mac(self, port) -> list:
        """
        Смотрим MAC'и на порту и отдаем в виде списка

        [ ["vlan", "mac"],  ... ]
        """

        port_type, indexes = self.split_port(port)

        # Для GPON ONT используем отдельный поиск
        if port_type == 'gpon' and len(indexes) == 4:
            data = self.__get_ont_port_info(indexes)  # Получаем информацию с порта абонента
            macs = []
            for service in data:
                if service.get('mac'):  # Если есть МАС для сервиса
                    macs.append([service.get('manage_vlan'), service['mac']])
            return macs

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
        # print(macs1+macs2)
        for m in macs1+macs2:
            res.append(m[::-1])
        return res

    @staticmethod
    def _up_down_command(port_type: str, status: str):
        """
        В зависимости от типа порта возвращает команды для управления его статусом
        """

        if port_type in ('scu', 'giu', 'gpon'):
            if status == 'down':
                return 'shutdown'
            if status == 'up':
                return 'undo shutdown'

        if port_type in ('adsl', 'ont'):
            if status == 'down':
                return 'deactivate'
            if status == 'up':
                return 'activate'

    def reload_port(self, port) -> str:
        """Перезагружаем порт"""

        port_type, indexes = self.split_port(port)

        if not port_type or len(indexes) not in [3, 4]:
            return f'Неверный порт! ({port})'

        self.session.sendline('config')
        self.session.sendline(f'interface {port_type} {indexes[0]}/{indexes[1]}')
        self.session.expect(self.prompt)

        if port_type == 'gpon' and len(indexes) == 4:
            # Перезагрузка ONT
            self.session.sendline(f'ont reset {indexes[2]} {indexes[3]}')
            self.session.sendline('y')
            self.session.expect(self.prompt)

        else:
            cmd = f"{self._up_down_command(port_type, 'down')} {indexes[2]}"  # Выключить порт
            self.session.sendline(cmd)
            self.session.expect(cmd)
            self.session.sendline('\n')
            sleep(1)  # Пауза

            cmd = f"{self._up_down_command(port_type, 'up')} {indexes[2]}"  # Включить порт
            self.session.sendline(cmd)
            self.session.expect(cmd)

            s = self.session.before.decode()

            self.session.sendline('\n')
            self.session.expect(r'\S+#$')

            s += self.session.before.decode()

        self.session.sendline('quit')
        return s

    def set_port(self, port, status) -> str:
        """
        Меняем состояние порта up/down

        В зависимости от типа порта команды разнятся

        Для порта adsl 0/1/2:
            # interface adsl 0/1
            # deactivate 2

        Для порта gpon 0/3/2/14:
            # interface gpon 0/3
            # ont port deactivate 2 14

        :param port: строка с портом (например: adsl 0/2/4)
        :param status: 'up' или 'down'
        :return:
        """

        port_type, indexes = self.split_port(port)

        if not port_type or len(indexes) not in [3, 4]:
            return f'Неверный порт! ({port})'

        self.session.sendline('config')
        self.session.sendline(f'interface {port_type} {indexes[0]}/{indexes[1]}')
        self.session.expect(self.prompt)

        if port_type == 'gpon' and len(indexes) == 4:
            # Для ONT
            s = self.send_command(
                f'ont port {self._up_down_command(port_type, status)} {indexes[2]} {indexes[3]}'
            )
            self.send_command('\n', expect_command=False)

        else:
            # Другие порты
            # Выключаем или включаем порт, в зависимости от типа будут разные команды
            s = self.send_command(
                f'{self._up_down_command(port_type, status)} {indexes[2]}',
                expect_command=False
            )
            self.send_command('\n', expect_command=False)

        self.session.sendline('quit')

        return s

    def get_interfaces(self) -> list:
        pass

    def get_vlans(self) -> list:
        pass

    def set_description(self, port: str, desc: str) -> str:
        """ Меняем описание на порту """

        port_type, indexes = self.split_port(port)
        if not port_type or len(indexes) != 3:
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

        return f'Description has been {"changed" if desc else "cleared"}.'


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
