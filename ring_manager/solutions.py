import check.models


# Класс Solutions предоставляет методы для настройки состояния портов и VLAN, а также для создания отчетов об ошибках и
# информационных сообщений.
class Solutions:
    def __init__(self):
        self.has_errors = False
        self._solutions = []

    def __len__(self):
        return len(self._solutions)

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

    def change_port(self, device: check.models.Devices, port: str, status: str, message: str):
        if not self.has_errors:
            self._solutions.append(
                {
                    "set_port_status": {
                        "status": status,
                        "device": device,
                        "port": port,
                        "message": message,
                    }
                }
            )

    def port_set_up(self, device: check.models.Devices, port: str, message: str):
        self.change_port(device, port, "up", message)

    def port_set_down(self, device: check.models.Devices, port: str, message: str):
        self.change_port(device, port, "down", message)

    def change_vlans(self, status: str, vlans: tuple, device: check.models.Devices, port: str, message: str):
        if not self.has_errors:
            self._solutions.append(
                {
                    "set_port_vlans": {
                        "status": status,
                        "vlans": vlans,
                        "device": device,
                        "port": port,
                        "message": message,
                    }
                }
            )

    def delete_vlans(self, vlans: tuple, device: check.models.Devices, port: str, message: str):
        self.change_vlans("delete", vlans, device, port, message)

    def add_vlans(self, vlans: tuple, device: check.models.Devices, port: str, message: str):
        self.change_vlans("add", vlans, device, port, message)
