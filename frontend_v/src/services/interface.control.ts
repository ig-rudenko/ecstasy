import {ref, Ref} from "vue";

import errorFmt from "@/errorFmt";
import {errorToast, newToast} from "@/services/my.toast";
import devicesService, {ChangePortStatusRequest} from "@/services/devices";

interface PortAction {
    device: string;
    name: string;
    action: string | null;
    port: string;
    desc: string;
}

class InterfaceControlService {
    public dialogVisible: Ref<boolean> = ref(false);

    public portAction: Ref<PortAction> = ref({
        device: "",
        name: "",
        action: "" as (string | null),
        port: "",
        desc: "",
    })

    closeDialog() {
        this.dialogVisible.value = false;
    }

    /**
     * Регистрируем действие над состоянием порта.
     * @param action Действие: ("up", "down", "reload")
     * @param port Название порта
     * @param description Описание порта
     * @param device Имя устройства
     */
    registerAction(action: "up" | "down" | "reload", port: string, description: string, device: string): void {

        if (["up", "down", "reload"].indexOf(action) < 0) {
            // Если неверное действие
            this.portAction.value = {
                device: "",
                name: "",
                action: null,
                port: "",
                desc: "",
            }
            this.dialogVisible.value = false;
            return;
        }

        let actionName: string
        if (action === "up") {
            actionName = "включить"
        } else if (action === "down") {
            actionName = "выключить"
        } else {
            actionName = "перезагрузить"
        }

        this.dialogVisible.value = true;
        this.portAction.value = {
            name: actionName,
            port: port,
            desc: description,
            action: action,
            device: device,
        }
    }


    /**
     * Подтверждаем действие над выбранным портом
     * @param saveConfig Сохранять конфигурацию?
     */
    submitPortAction(saveConfig: boolean): void {
        this.dialogVisible.value = false;

        if (!this.portAction.value.action) return;

        let data: ChangePortStatusRequest = {
            port: this.portAction.value.port,       // Сам порт
            desc: this.portAction.value.desc,       // Описание порта
            status: this.portAction.value.action,   // Что сделать с портом
            save: saveConfig,                 // Сохранить конфигурацию после действия?
        }

        devicesService.changePortStatus(this.portAction.value.device, data)
            .then(
                value => {
                    let status = value.status.toUpperCase();
                    let className = status === "DOWN" ? "bg-red-500" : (status === "RELOAD" ? "bg-orange-500" : "bg-green-600");
                    status = status === "DOWN" ? "ADMIN DOWN" : status;
                    newToast(
                        `Порт: <span class="p-badge bg-gray-700 text-white">${value.port}</span>`,
                        `Состояние: <span class="p-badge ${className}">${status}</span>
                           Конфигурация ${value.save ? '' : 'НЕ '}была сохранена!`,
                        value.save ? "success" : "info",
                        5000,
                    )
                },
                (reason: any) => errorToast("Ошибка при изменении состояния порта", errorFmt(reason))
            )
            .catch(
                (reason: any) => errorToast("Ошибка при изменении состояния порта", errorFmt(reason))
            )
    }

}


const interfaceControlService = new InterfaceControlService();
export default interfaceControlService;