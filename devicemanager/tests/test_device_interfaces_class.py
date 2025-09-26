from django.test import SimpleTestCase

from devicemanager.device import Interfaces
from devicemanager.device.interfaces import Interface


class TestInterfacesClass(SimpleTestCase):
    def test_interface_init(self):
        # Создание списка интерфейсов.
        interfaces_list = [
            ["eth1", "up", "description1"],
            ["eth2", "down", "description2"],
            ["eth3", "admin down", "description3"],
            ["eth4", "up", "description4"],
        ]
        # Создание нового экземпляра класса Interfaces.
        intf = Interfaces(interfaces_list)

        # Проверка того, что второй элемент существует и он верный.
        self.assertEqual(str(intf[1]), str(Interface(*interfaces_list[1])))
        # Проверяем, что количество интерфейсов равно 4.
        self.assertEqual(intf.count, 4)
        # Проверяем, что количество интерфейсов со статусом up равно 2.
        self.assertEqual(intf.up(only_count=True), 2)
        # Проверяем, что количество интерфейсов со статусом down равно 1.
        self.assertEqual(intf.down(only_count=True), 2)
        # Проверяем, что количество интерфейсов со статусом admin_down равно 1.
        self.assertEqual(intf.admin_down(only_count=True), 1)

        # Проверка того, что метод with_vlans возвращает правильный интерфейс.
        self.assertEqual(str(intf.with_vlans([11])), str(Interfaces()))

        # Проверка того, что метод filter_by_desc возвращает правильный ответ.
        self.assertEqual(str(intf.filter_by_desc("description")), str(intf))
        # Проверка того, что метод filter_by_desc возвращает правильный ответ.
        self.assertEqual(
            str(intf.filter_by_desc("description2")),
            str(Interfaces([interfaces_list[1]])),
        )
        # Проверка того, что метод filter_by_desc возвращает правильный ответ.
        # Для не существующего результата по фильтру описания
        self.assertEqual(str(intf.filter_by_desc("invalid")), str(Interfaces()))

        interfaces_as_dict_list = [
            {"name": "eth1", "status": "up", "description": "description1"},
            {"name": "eth2", "status": "down", "description": "description2"},
            {
                "name": "eth3",
                "status": "admin down",
                "description": "description3",
            },
            {"name": "eth4", "status": "up", "description": "description4"},
        ]
        # Сравниваем, что интерфейсы созданные на основе списков и на основе словарей дают одинаковые данные.
        self.assertEqual(str(Interfaces(interfaces_as_dict_list)), str(Interfaces(interfaces_list)))

    def test_interface_init_vlans(self):
        # Создание списка интерфейсов.
        interfaces_list = [
            ["eth1", "up", "description1", [11, 21]],
            ["eth2", "down", "description2", [12, 22]],
            ["eth3", "admin down", "description3", [13, 23]],
            ["eth4", "up", "description4", [14, 24]],
        ]
        # Создание нового экземпляра класса Interfaces.
        intf = Interfaces(interfaces_list)

        # Проверка того, что второй элемент существует и он верный.
        self.assertEqual(str(intf[1]), str(Interface(*interfaces_list[1])))
        # Проверяем, что количество интерфейсов равно 4.
        self.assertEqual(intf.count, 4)
        # Проверяем, что количество интерфейсов со статусом up равно 2.
        self.assertEqual(intf.up(only_count=True), 2)
        # Проверяем, что количество интерфейсов со статусом down равно 1.
        self.assertEqual(intf.down(only_count=True), 2)
        # Проверяем, что количество интерфейсов со статусом admin_down равно 1.
        self.assertEqual(intf.admin_down(only_count=True), 1)
        # Проверка того, что метод with_vlans возвращает правильный интерфейс.
        self.assertEqual(str(intf.with_vlans([11])), str(Interfaces([interfaces_list[0]])))
        # Проверка того, что метод filter_by_desc возвращает правильный ответ.
        self.assertEqual(str(intf.filter_by_desc("description")), str(intf))
        # Проверка того, что метод filter_by_desc возвращает правильный ответ.
        self.assertEqual(
            str(intf.filter_by_desc("description2")),
            str(Interfaces([interfaces_list[1]])),
        )
        # Проверка того, что метод filter_by_desc возвращает правильный ответ.
        # Для не существующего результата по фильтру описания
        self.assertEqual(str(intf.filter_by_desc("invalid")), str(Interfaces()))

        interfaces_dict = [
            {
                "name": "eth1",
                "status": "up",
                "description": "description1",
                "vlans": [11, 21],
            },
            {
                "name": "eth2",
                "status": "down",
                "description": "description2",
                "vlans": [12, 22],
            },
            {
                "name": "eth3",
                "status": "admin down",
                "description": "description3",
                "vlans": [13, 23],
            },
            {
                "name": "eth4",
                "status": "up",
                "description": "description4",
                "vlans": [14, 24],
            },
        ]
        # Сравниваем, что интерфейсы созданные на основе списков и на основе словарей дают одинаковые данные.
        self.assertEqual(str(Interfaces(interfaces_dict)), str(Interfaces(interfaces_list)))

    def test_interface_init_mixed_interface_list(self):
        # Создание списка интерфейсов.
        interfaces_list = [
            ["eth1", "up", "description1", [11, 21]],
            ["eth2", "down", "description2", [12, 22]],
            ["eth3", "admin down", "description3", [13, 23]],
            ["eth4", "up", "description4", [14, 24]],
        ]
        # Создание смешанного списка интерфейсов.
        interfaces_mixed = [
            ["eth1", "up", "description1", [11, 21]],
            {
                "name": "eth2",
                "status": "down",
                "description": "description2",
                "vlans": [12, 22],
            },
            ["eth3", "admin down", "description3", [13, 23]],
            {
                "name": "eth4",
                "status": "up",
                "description": "description4",
                "vlans": [14, 24],
            },
        ]
        # Сравниваем, что интерфейсы созданные на основе списков и на смешанной основе дают одинаковые данные.
        self.assertEqual(str(Interfaces(interfaces_mixed)), str(Interfaces(interfaces_list)))
