import re
from time import sleep
from .base import BaseDevice


class IskratelControl(BaseDevice):
    """
    Для плат управления DSLAM от производителя Iskratel
    """

    prompt = r'\(\S+\)\s*#'
    space_prompt = r'--More-- or \(q\)uit'
    mac_format = r'\S\S:'*5+r'\S\S'
    vendor = 'Iskratel'

    def save_config(self):
        pass

    def get_mac(self, port) -> list:
        """
        Смотрим MAC'и на порту и отдаем в виде списка

        [ ["vlan", "mac"],  ... ]
        """

        if not re.findall(r'\d+/\d+', port):  # Неверный порт
            return []

        output = self.send_command(f'show mac-addr-table interface {port}')
        macs = re.findall(rf'({self.mac_format})\s+(\d+)', output)

        res = []
        for m in macs:
            res.append(m[::-1])
        return res

    def get_interfaces(self) -> list:
        pass

    def get_vlans(self) -> list:
        pass

    def reload_port(self, port) -> str:
        pass

    def set_port(self, port: str, status: str) -> str:
        pass

    def set_description(self, port: str, desc: str) -> str:
        pass


class IskratelMBan(BaseDevice):
    """
    Для плат DSLAM от производителя Iskratel

    Проверено для:
     - MPC8560
    """

    prompt = r'mBAN>\s'
    space_prompt = r'Press any key to continue or Esc to stop scrolling\.'
    mac_format = r'\S\S:'*5+r'\S\S'
    vendor = 'Iskratel'

    def save_config(self):
        pass

    @property
    def get_service_ports(self):
        """ Сервисные порты для DSLAM """
        return ['1_32', '1_33', '1_40']

    def port_info_parser(self, info: str) -> str:
        """
        Парсит информацию о порте DSL и создает таблицу html для представления показателей сигнал/шума, затухания,
        мощности и прочей информации
        """

        def color(val: str, s: str) -> str:
            if not val:
                return ''
            val = float(val)

            """ Определяем цвета в зависимости от числовых значений показателя """
            if 'Сигнал/Шум' in s:
                gradient = [5, 7, 10, 20]
            elif 'Затухание линии' in s:
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
        names = ['Фактическая скорость передачи данных (Кбит/с)', 'Максимальная скорость передачи данных (Кбит/с)',
                 'Сигнал/Шум (дБ)', 'Interleaved channel delay (ms)', 'Затухание линии (дБ)']

        oper_state = self.find_or_empty(r'Operational State\s+(\S+)\/', info)
        if self.find_or_empty(r'Equipment\s+Unequipped', info):
            html += '<p style="color: red">Порт - ADMIN DOWN</p>'
        elif oper_state == 'Down':
            html += '<p>Порт - DOWN</p>'
        elif oper_state == 'Up':
            html += '<p style="color: green">Порт - UP</p>'

        html += f'<p>'+self.find_or_empty(r"Type .*", info)+'</p>'
        html += f'<p>'+self.find_or_empty(r"Profile Name\s+\S+", info)+'</p>'

        # Данные для таблицы
        data_rate = re.findall(r'DS Data Rate AS0\s+(\d+) kbit/s\s+US Data Rate LS0\s+(\d+) kbit', info) or [('', '')]
        max_rate = [(self.find_or_empty(r'Maximum DS attainable aggregate rate\s+(\d+) kbit', info),
                    self.find_or_empty(r'Maximum US attainable aggregate rate\s+(\d+) kbit', info))]

        snr = re.findall(r'DS SNR Margin\s+(\d+) dB\s+US SNR Margin\s+(\d+)', info) or [('', '')]
        intl = re.findall(r'DS interleaved delay\s+(\d+) ms\s+US interleaved delay\s+(\d+)', info) or [('', '')]
        att = re.findall(r'DS Attenuation\s+(\d+) dB\s+US Attenuation\s+(\d+)', info) or [('', '')]

        # Наполняем таблицу
        for line in zip(names, data_rate + max_rate + snr + intl + att):
            table += f"""
            <tr>
                <td style="text-align: right";>{line[0]}</td>
                <td style="text-align: center; background-color: {color(line[1][0], line[0])};">{line[1][0]}</td>
                <td style="text-align: center; background-color: {color(line[1][1], line[0])};">{line[1][1]}</td>
            </tr>
            """
        else:
            table += "</tbody></table></div>"  # Закрываем таблицу

        html += '</div>'  # Закрываем первую колонку
        html += table     # Добавляем вторую колонку - таблицу
        html += '</div>'  # Закрываем ряд
        return html

    def get_port_info(self, port: str):
        port = port.strip()
        # Верные порты: port1, fasteth3, adsl2:1_40
        if not re.findall(r'^port\d+$|^fasteth\d+$|^dsl\d+:\d+_\d+$', port):
            return ''

        if 'port' in port:  # Если указан физический adsl порт
            cmd = f'show dsl port {port[4:]} detail'
            before_catch = r'Name\s+\S+'
        else:
            cmd = f'show interface {port}'
            before_catch = r'\[Enabled Connected Bridging\]'

        output = self.send_command(cmd, expect_command=False, before_catch=before_catch)
        return self.port_info_parser(output)

    def get_mac(self, port: str) -> list:
        """
        Смотрим MAC'и на порту и отдаем в виде списка

        [ ["vlan", "mac"],  ... ]
        """

        port = port.strip()
        macs = []  # Итоговый список маков

        # Верные порты: port1, fasteth3, dsl2:1_40, ISKRATEL:sv-263-3443 atm 2/1
        if not re.findall(r'^port\d+$|^fasteth\d+$|^dsl\d+:\d+_\d+$|^ISKRATEL.*atm \d+/\d+$', port):
            return []

        if 'fasteth' in port or 'adsl' in port:
            output = self.send_command(f'show bridge mactable interface {port}', expect_command=False)
            macs = re.findall(rf'(\d+)\s+({self.mac_format})', output)
            return macs

        elif 'port' in port:  # Если указан физический adsl порт
            port = port[4:]  # убираем слово port, оставляя только номер

        elif 'ISKRATEL' in port:
            port = self.find_or_empty(r'\d+$', port)
            if not port:
                return []

        for sp in self.get_service_ports:  # смотрим маки на сервис портах
            output = self.send_command(f'show bridge mactable interface dsl{port}:{sp}', expect_command=False)
            macs.extend(re.findall(rf'(\d*)\s+({self.mac_format})', output))

        return macs

    @staticmethod
    def validate_port(port: str):
        """
        Проверяем правильность полученного порта
        Для Iskratel порт должен быть числом

        port23 -> 23

        """
        port = port.strip()

        if 'ISKRATEL' in port:
            port = re.findall(r'\d+$', port)
        else:
            port = re.findall(r'^port(\d+)$', port)

        if port:
            return port[0]

    def reload_port(self, port: str) -> str:
        port = self.validate_port(port)
        if port is None:
            return f'Неверный порт!'

        s1 = self.send_command(f'set dsl port {port} port_equp unequipped', expect_command=False)
        sleep(1)
        s2 = self.send_command(f'set dsl port {port} port_equp equipped', expect_command=False)

        return s1 + s2

    def set_port(self, port: str, status: str):
        port = self.validate_port(port)
        if port is None:
            return f'Неверный порт!'

        # Меняем состояние порта
        return self.send_command(
            f'set dsl port {port} port_equp {"equipped" if status == "up" else "unequipped"}',
            expect_command=False
        )

    def get_interfaces(self) -> list:
        output = self.send_command(f'show dsl port', expect_command=False)
        res = []
        for line in output.split('\n'):
            interface = re.findall(r'(\d+)\s+(\S+)\s+\S+\s+(Equipped|Unequipped)\s+(Up|Down|)', line)
            if interface:
                res.append([
                    interface[0][0],    # name
                    interface[0][3].lower() if interface[0][2] == 'Equipped' else 'admin down',
                    interface[0][1],    # desc
                ])

        return res

    def get_vlans(self) -> list:
        return self.get_interfaces()

    def set_description(self, port: str, desc: str) -> str:
        port = self.validate_port(port)
        if port is None:
            return f'Неверный порт!'

        desc = self.clear_description(desc)

        if len(desc) > 32:
            return 'Max length:32'

        self.send_command(f'set dsl port {port} name {desc}', expect_command=False)

        return f'Description has been {"changed" if desc else "cleared"}.'
