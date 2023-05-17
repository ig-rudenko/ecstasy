from datetime import timedelta, datetime
from typing import Literal, Sequence, Dict, Tuple

import check.models
from devicemanager import DeviceException
from devicemanager.device import Interfaces
from .models import TransportRing


class Solutions:
    """
    Класс Solutions предоставляет методы для настройки состояния портов и VLAN, а также для создания отчетов об ошибках
    и информационных сообщений.
    """

    # Категории решений, которые не затрагивают работу кольца
    safe_solutions = {"info", "error"}

    # Категории решений, которые изменяют поведение оборудований в кольце
    affect_solutions = {"set_port_status", "set_port_vlans"}

    def __init__(self):
        self.has_errors = False
        self._solutions = []

        # Показывает, являются ли сформированные решения безопасными, т.е. их не требуется выполнять.
        # Безопасными считаются информационные (info, error)
        self.has_only_safe_solutions = True

    def __len__(self):
        return len(self._solutions)

    @classmethod
    def from_ring_history(cls, ring: TransportRing) -> "Solutions":
        sm = Solutions()
        if not ring.solutions:
            return sm

        if isinstance(ring.solutions, Sequence):
            for solution in ring.solutions:
                if set(solution).issubset(cls.affect_solutions):
                    sm.has_only_safe_solutions = False
                sm._solutions.append(solution)

        return sm

    @property
    def solutions(self) -> tuple:
        return tuple(self._solutions)

    def error(self, status: str, message: str):
        self._solutions = [
            {
                "error": {
                    "status": status,
                    "message": message,
                },
            }
        ]
        self.has_errors = True

    def info(self, message: str):
        self._solutions.append(
            {
                "info": {
                    "message": message,
                }
            }
        )

    def _change_port(
        self, device: check.models.Devices, port: str, status: Literal["up", "down"], message: str
    ):
        if not self.has_errors:
            self.has_only_safe_solutions = False
            self._solutions.append(
                {
                    "set_port_status": {
                        "status": status,
                        "device": {
                            "name": device.name,
                            "ip": device.ip,
                        },
                        "port": port,
                        "message": message,
                    }
                }
            )

    def port_set_up(self, device: check.models.Devices, port: str, message: str):
        """
        Переводит указанный порт устройства в состояние `admin up`.
        """
        self._change_port(device, port, "up", message)

    def port_set_down(self, device: check.models.Devices, port: str, message: str):
        """
        Переводит указанный порт устройства в состояние `admin down`.
        """
        self._change_port(device, port, "down", message)

    def _change_vlans(
        self,
        status: Literal["add", "delete"],
        vlans: Tuple[int],
        device: check.models.Devices,
        port: str,
        message: str,
    ):
        if not self.has_errors:
            self.has_only_safe_solutions = False
            self._solutions.append(
                {
                    "set_port_vlans": {
                        "status": status,
                        "vlans": vlans,
                        "device": {
                            "name": device.name,
                            "ip": device.ip,
                        },
                        "port": port,
                        "message": message,
                    }
                }
            )

    def delete_vlans(
        self, vlans: Tuple[int], device: check.models.Devices, port: str, message: str
    ):
        """
        Удаляет указанные VLAN на порту данного устройства.
        """
        self._change_vlans("delete", vlans, device, port, message)

    def add_vlans(self, vlans: Tuple[int], device: check.models.Devices, port: str, message: str):
        """
        Добавляет указанные VLAN на порт данного устройства.
        """
        self._change_vlans("add", vlans, device, port, message)


class SolutionsPerformerError(Exception):
    def __init__(self, message: str):
        self.message = message


class SolutionsPerformer:
    """
    Выполняет операции с сетевыми устройствами, такие как установка состояния порта и VLAN,
    с обработкой ошибок и логикой повторных попыток.
    """

    # Используется в качестве срока жизни (TTL) для решений, что означает, если решения были созданы ранее
    # указанного времени, они будут считаться просроченным и не станут выполняться.
    solution_expire: timedelta = timedelta(minutes=1)

    def __init__(self, ring: TransportRing):
        self.ring = ring

        if not self.ring.solutions:
            raise SolutionsPerformerError("Нет решений, которые необходимо выполнить")

        if self.is_solution_expired(self.ring.solution_time):
            # Этот код проверяет, является ли время создания решений (сохраненное в `self.ring.solution_time`)
            # более ранним чем текущее время минус время истечения срока действия решений (`self.solution_expire`).
            # Это делается для того, чтобы решения выполнялись своевременно и не применялись к сети после того, как они
            # перестали быть актуальными.
            raise SolutionsPerformerError("Решения просрочены, необходимо заново сформировать их")

        if not isinstance(self.ring.solutions, Sequence):
            raise SolutionsPerformerError(
                f"Неправильный тип для решений, ожидается `Sequence`, а был передан {type(self.ring.solutions)}"
            )
        else:
            self.solutions: Sequence = self.ring.solutions

    @classmethod
    def is_solution_expired(cls, solution_time: datetime) -> bool:
        """
        Эта функция проверяет, истекло ли заданное время решения или нет.

        :param solution_time: параметр типа «datetime», представляющий время создания или последнего обновления решения.
        """
        return not solution_time or solution_time < datetime.now() - cls.solution_expire

    def perform_all(self) -> Sequence[dict]:
        """
        Эта функция выполняет конвейер решений, и если возникает ошибка, она пытается выполнить конвейер в обратном
         порядке, начиная с последнего успешного решения.
        :return: список решений, хранящихся в атрибуте self.solutions экземпляра класса.
        """

        counter = {"normal": 0, "reversed": 0}

        try:
            # Выполняем все решения по очереди
            self._perform_pipeline(self.solutions, counter=counter)
        except SolutionsPerformerError:
            # Если в одном из решений произошла ошибка, то необходимо откатить примененные изменения
            try:
                # Устанавливает переменную `position` в индекс последнего успешно выполненного решения и снова выполняет
                # конвейер в обратном порядке, начиная с этой позиции.

                if counter["normal"]:
                    position = counter["normal"] - 1

                    self._perform_pipeline(
                        self.solutions[position::-1], counter=counter, reverse_status=True
                    )

            except SolutionsPerformerError:
                return self.solutions

        return self.solutions

    def _perform_pipeline(
        self, solutions: Sequence[dict], counter: Dict[str, int], reverse_status: bool = False
    ):
        """
        Эта функция выполняет конвейер решений, проверяя их безопасность и выполняя их в зависимости от их типа.

        :param solutions: последовательность словарей, представляющих решения, которые необходимо выполнить
        :param counter: Словарь счетчиков "normal" и "reversed" для подсчета кол-ва выполненных решений в pipeline
        :param reverse_status: Логический параметр, определяющий, следует ли обратить все действия в решениях.
        """

        counter_name = "reversed" if reverse_status else "normal"

        for solution in solutions:

            # Этот код проверяет, являются ли ключи в словаре «solution» подмножеством списка «safe_solutions»
            # в классе «Solutions». Если они есть, это означает, что решение безопасно и не требует каких-либо
            # действий. Оператор continue пропускает текущую итерацию цикла и переходит к следующему решению.
            if set(solution).issubset(Solutions.safe_solutions):
                counter[counter_name] += 1
                continue

            # `tuple(solution)` создает кортеж из ключей словаря `solution`. `tuple(solution)[0]` затем извлекает
            # первый элемент (т.е. первый ключ) этого кортежа, который представляет тип выполняемого решения
            # (например, "set_port_status", "set_port_vlans"). Это используется для определения того, какое
            # действие следует предпринять в методе `perform`.
            solution_type = tuple(solution)[0]

            try:
                if solution_type == "set_port_status":
                    self.perform_port_status(
                        **solution[solution_type], reverse_status=reverse_status
                    )

                elif solution_type == "set_port_vlans":
                    self.perform_vlans(**solution[solution_type], reverse_status=reverse_status)

            except SolutionsPerformerError as error:
                # Помечаем статус данного решения, как ошибка
                solution[solution_type]["perform_status"] = "fail"
                solution[solution_type]["error"] = error.message
                raise

            # Помечаем статус решения "reversed" или "done"
            solution[solution_type]["perform_status"] = "reversed" if reverse_status else "done"

            # Выполнили решение
            counter[counter_name] += 1

    @staticmethod
    def _get_device(device: Dict[str, str]) -> check.models.Devices:
        """
        Это функция Python, которая принимает словарь, представляющий устройство, и возвращает объект типа
        check.models.Devices.

        :param device: Параметр `device` представляет собой словарь, содержащий информацию об устройстве
         {"ip": "", "name": ""}
        """
        # Проверяет, является ли параметр `device`, словарем с ключами `name` и `ip`.
        if set(device) != {"name", "ip"}:
            raise SolutionsPerformerError(
                f"Для изменения состояния порта оборудование необходимо передавать в виде словаря"
                f" с ключами `name` и `ip`, а было передано {device}"
            )
        try:
            # Метод `select_related` используется для оптимизации запроса путем выборки связанных объектов
            # (в данном случае `auth_group`) в одном запросе к базе данных
            return check.models.Devices.objects.select_related("auth_group").get(
                ip=device["ip"], name=device["name"]
            )

        except check.models.Devices.DoesNotExist as error:
            # from error используется для сохранения исходного исключения (DoesNotExist)
            # в качестве причины нового исключения (SolutionsPerformerError).
            raise SolutionsPerformerError(
                f"Не было найдено оборудование в базе с IP={device['ip']} и name={device['name']}"
            ) from error

    def perform_vlans(
        self,
        status: Literal["add", "delete"],
        device: Dict[str, str],
        port: str,
        vlans: Sequence[int],
        message: str = "",
        reverse_status: bool = False,
        **kwargs,
    ):
        """
        Выполняет операции по добавлению или удалению VLAN на порту сетевого устройства с
        обработкой ошибок и логикой повторных попыток.

        :param status: Параметр состояния — это строковый литерал, который может иметь только значения «add» или
         «delete». Он используется для указания, следует ли добавлять или удалять VLAN из порта сетевого устройства.
        :param device: Параметр `device` представляет собой словарь, содержащий информацию о сетевом устройстве,
         на котором должна выполняться операция VLAN. Он должен иметь ключи `name` и `ip`.
        :param port: Параметр `port` представляет собой строку, представляющую сетевой порт на устройстве,
         где VLAN будут добавлены или удалены
        :param vlans: Параметр `vlans` представляет собой последовательность целых чисел, представляющих VLAN, которые
         необходимо добавить или удалить из сетевого порта на устройстве.
        :param message: Параметр `message` — необязательный строковый параметр, который можно использовать для
         предоставления дополнительной информации или контекста для выполняемой операции VLAN.
         Он имеет значение по умолчанию пустой строки
        :param reverse_status: (optional) Необходимо ли обратить переданный `status` (default = False)
        """

        if status not in ("add", "delete"):
            raise SolutionsPerformerError(
                f"Для изменения VLAN на порту его оператор должен быть `add` либо `delete`, а был передан `{status}`"
            )

        if not isinstance(vlans, (tuple, list)) or any(map(lambda v: type(v) != int, vlans)):
            raise SolutionsPerformerError(
                "параметр `vlans` должен быть типом `list` или `tuple`, а также содержать в себе список целых чисел,"
                f" а был передан {vlans}, Type: {type(vlans)}"
            )

        # Если `reverse_status` равно True, то значение `status` будет переключено на противоположное его
        # текущему значению. Если `reverse_status` равно False, то значение `status` останется прежним.
        if reverse_status:
            status = "add" if status == "delete" else "delete"

        device_obj = self._get_device(device)

        if not device_obj.available:
            raise SolutionsPerformerError(f"Оборудование {device_obj} недоступно")

        try:
            with device_obj.connect() as conn:

                tries = 2
                while tries:
                    # Этот цикл используется для повторной попытки кон VLANS в случае сбоя.
                    # Цикл будет выполняться не более `tries = 2` раз.

                    if hasattr(conn, "vlans_on_port"):
                        conn.vlans_on_port(port=port, operation=status, vlans=vlans)
                    else:
                        raise SolutionsPerformerError(
                            f"Оборудование {device_obj}, vendor={conn.vendor} не имеет метода "
                            f"для управления VLAN на порту"
                        )

                    tries -= 1

                    # Приведенный выше код проверяет наличие или отсутствие набора VLAN на определенном сетевом
                    # интерфейсе.
                    # Он делает это, сначала извлекая существующие сети VLAN на интерфейсе.
                    interfaces = Interfaces(conn.get_vlans())

                    # А затем проверяя, является ли набор добавляемых или удаляемых сетей VLAN подмножеством
                    # существующих сетей VLAN на интерфейсе.

                    # Если нужно добавить, но VLAN не были добавлены к порту, переходит к следующей попытке добавить.
                    if status == "add" and not set(vlans).issubset(set(interfaces[port].vlan)):
                        continue
                    # Если нужно удалить, но VLAN присутствуют на порту, переходит к следующей попытке удаления.
                    elif status == "delete" and set(vlans).issubset(set(interfaces[port].vlan)):
                        continue

                    # Если операция прошла успешно, то выходим из цикла
                    else:
                        break

                else:
                    # Этот блок «else» выполняется, когда цикл завершает все итерации, не встречая оператора «break».
                    # В этом случае это означает,
                    # что операция добавления или удаления VLAN к/от порта устройства не удалась.
                    raise SolutionsPerformerError(
                        f"Не удалось {status} VLANS - {vlans} в на оборудовании {device_obj} на порт {port}"
                    )

        except DeviceException as error:
            raise SolutionsPerformerError(
                f"Оборудование {device_obj} вызвало ошибку {error.message}"
            ) from error

    def perform_port_status(
        self,
        status: Literal["up", "down"],
        device: Dict[str, str],
        port: str,
        message: str = "",
        reverse_status: bool = False,
        **kwargs
    ):
        """
        Это функция Python, которая выполняет обновление состояния порта для заданного устройства.

        :param status: Требуемый статус порта, который представляет собой строковое значение.
         Это может быть «up» или «down»
        :param device: Параметр `device` представляет собой словарь, содержащий информацию о сетевом устройстве.
         Он должен включать такие атрибуты, как IP-адрес устройства и его имя.
        :param port: Строка, представляющая имя или идентификатор сетевого порта на устройстве.
        :param message: Параметр «message» — это необязательный строковый параметр, который можно передать в метод
         «perform_port_status». Он используется для предоставления дополнительной информации или контекста об изменении
         состояния порта, о котором сообщается. Если сообщение не предоставлено, в качестве значения по умолчанию будет
         использоваться пустая строка
        :param reverse_status: (optional) Необходимо ли обратить переданный `status` (default = False)
        """
        if status not in ("up", "down"):
            raise SolutionsPerformerError(
                f"Для изменения состояния порта его статус должен быть `up` либо `down`, а был передан `{status}`"
            )

        # Если `reverse_status` равно True, то значение `status` будет переключено на противоположное его
        # текущему значению. Если `reverse_status` равно False, то значение `status` останется прежним.
        if reverse_status:
            status = "up" if status == "down" else "down"

        device_obj = self._get_device(device)

        if not device_obj.available:
            raise SolutionsPerformerError(f"Оборудование {device_obj} недоступно")

        try:
            with device_obj.connect() as conn:

                tries = 2
                while tries:
                    # Этот цикл используется для повторной попытки установить статус порта в случае сбоя.
                    # Цикл будет выполняться не более `tries = 2` раз.

                    result = conn.set_port(port=port, status=status, save_config=True)
                    if result == "Неверный порт":
                        raise SolutionsPerformerError(
                            f"Неверный порт {port} для оборудования {device_obj}"
                        )

                    tries -= 1

                    # Этот блок кода проверяет текущее состояние порта на устройстве и сравнивает его с желаемым
                    # состоянием (включено или выключено).
                    # Сначала он извлекает интерфейсы из устройства.
                    interfaces = Interfaces(conn.get_interfaces())

                    # Если желаемое состояние порта - «down» и он не отключен административно,
                    # то переходит к следующей попытке, чтобы снова попытаться установить статус порта в «down».
                    if status == "down" and not interfaces[port].is_admin_down:
                        continue

                    # Точно так же, если желаемое состояние - «up», а порт административно выключен,
                    # то переходит к следующей попытке, чтобы снова попытаться установить статус порта в «up».
                    elif status == "up" and interfaces[port].is_admin_down:
                        continue

                    # Если ни одно из этих условий не выполняется, то выходим из цикла.
                    else:
                        break

                else:
                    # Этот блок «else» выполняется, когда цикл завершает все итерации, не встречая оператора «break».
                    # В этом случае это означает, что требуемый статус порта не может быть установлен на устройстве
                    # после максимального количества повторных попыток (2).
                    raise SolutionsPerformerError(
                        f"Не удалось установить состояние порта {port} в {status} на оборудовании {device_obj}"
                    )

        except DeviceException as error:
            raise SolutionsPerformerError(
                f"Оборудование {device_obj} вызвало ошибку {error.message}"
            ) from error
