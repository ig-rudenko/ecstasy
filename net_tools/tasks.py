import orjson

from celery.result import AsyncResult
from django.utils import timezone
from django.core.cache import cache

from ecstasy_project.celery import app
from ecstasy_project.task import ThreadUpdatedStatusTask
from check.models import Devices as ModelDevices, AuthGroup
from devicemanager.device import DeviceManager
from net_tools.models import DevicesInfo


class InterfacesScanTask(ThreadUpdatedStatusTask):
    name = "interfaces_scan"
    queryset = ModelDevices.objects.all()

    def pre_run(self):
        super().pre_run()
        cache.set("periodically_scan_id", self.request.id, timeout=None)

    def thread_task(self, obj: ModelDevices, **kwargs):
        dev = DeviceManager.from_model(obj)

        if not obj.available:
            # Если оборудование недоступно, то пропускаем
            return

        # Собираем интерфейсы
        status = dev.collect_interfaces(vlans=True, current_status=True, make_session_global=False)

        model_update_fields = []  # Поля для обновлений, в случае изменения записи в БД

        # Если пароль неверный, то пробуем все по очереди, кроме уже введенного
        if "Неверный логин или пароль" in str(status):

            # Создаем список объектов авторизации
            al = list(AuthGroup.objects.exclude(name=obj.auth_group.name).order_by("id").all())

            # Собираем интерфейсы снова
            status = dev.collect_interfaces(vlans=True, current_status=True, auth_obj=al)

            if status is None:  # Если статус сбора интерфейсов успешный
                # Необходимо перезаписать верный логин/пароль в БД, так как первая попытка была неудачной
                try:
                    # Смотрим объект у которого такие логин и пароль
                    a = AuthGroup.objects.get(
                        login=dev.success_auth["login"],
                        password=dev.success_auth["password"],
                    )

                except (TypeError, ValueError, AuthGroup.DoesNotExist):
                    # Если нет такого объекта, значит нужно создать
                    a = AuthGroup.objects.create(
                        name=dev.success_auth["login"],
                        login=dev.success_auth["login"],
                        password=dev.success_auth["password"],
                        secret=dev.success_auth["privilege_mode_password"],
                    )

                # Указываем новый логин/пароль для этого устройства
                obj.auth_group = a
                # Добавляем это поле в список изменений
                model_update_fields.append("auth_group")

        # Обновляем модель устройства, взятую непосредственно во время подключения, либо с Zabbix
        # dev.zabbix_info.inventory.model обновляется на основе реальной модели при подключении
        if dev.zabbix_info.inventory.model and dev.zabbix_info.inventory.model != obj.model:
            obj.model = dev.zabbix_info.inventory.model
            model_update_fields.append("model")

        # Обновляем вендора оборудования, если он отличается от реального либо еще не существует
        if dev.zabbix_info.inventory.vendor and dev.zabbix_info.inventory.vendor != obj.vendor:
            obj.vendor = dev.zabbix_info.inventory.vendor
            model_update_fields.append("vendor")

        # Сохраняем изменения
        if model_update_fields:
            obj.save(update_fields=model_update_fields)
        if not dev.interfaces.count:
            return

        # Сохраняем интерфейсы
        try:
            current_device_info = DevicesInfo.objects.get(dev=obj)
        except DevicesInfo.DoesNotExist:
            current_device_info = DevicesInfo.objects.create(dev=obj)

        vlans_interfaces_to_save = [
            {
                "Interface": line.name,
                "Status": line.status,
                "Description": line.desc,
                "VLAN's": line.vlan,
            }
            for line in dev.interfaces
        ]
        current_device_info.vlans = orjson.dumps(vlans_interfaces_to_save).decode()
        current_device_info.vlans_date = timezone.now()
        print(f"Saved VLANS   -->  {obj}")

        interfaces_to_save = [
            {
                "Interface": line.name,
                "Status": line.status,
                "Description": line.desc,
            }
            for line in dev.interfaces
        ]
        current_device_info.interfaces = orjson.dumps(interfaces_to_save).decode()
        current_device_info.interfaces_date = timezone.now()

        current_device_info.save()
        print(f"Saved Interfaces   -->  {obj}")

        self.update_state()


interfaces_scan = app.register_task(InterfacesScanTask())


def check_scanning_status() -> dict:
    task_id = cache.get("periodically_scan_id")
    if task_id:
        task = AsyncResult(str(task_id))
        if task.status == "PENDING":
            return {"status": "PENDING"}
        if task.status == "PROGRESS":
            return {"status": "PROGRESS", "progress": task.result.get("progress", "~")}

        cache.delete("periodically_scan_id")

    return {
        "status": None,
    }
