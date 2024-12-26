import api from "@/services/api";
import errorFmt from "@/errorFmt";
import {errorToast} from "@/services/my.toast";
import {InterfacesCount} from "@/services/interfaces";


export interface Device {
    ip: string;
    name: string;
    model: string;
    group: string;
    vendor: string;
    port_scan_protocol: string;
    interfaces_count?: InterfacesCount;
}

export interface DevicesWithCount {
    devices: Device[];
    devices_count: number;
}

export interface ChangePortStatusRequest {
    port: string;
    desc: string;
    status: string;
    save: boolean;
}

export interface ChangePortStatusResponse {
    port: string;
    status: string;
    save: boolean;
}


export class DevicesService {


    async getDevicesList(): Promise<Device[]> {
        try {
            let resp = await api.get<Device[]>("/api/v1/devices/");
            return resp.data;
        } catch (reason: any) {
            errorToast("Не удалось получить список устройств", errorFmt(reason))
            return [];
        }
    }

    async getDevicesListWithInterfacesWorkload(): Promise<Device[]> {
        try {
            let resp = await api.get<DevicesWithCount>("/api/v1/devices/workload/interfaces");
            return resp.data.devices;
        } catch (reason: any) {
            errorToast("Не удалось получить список устройств", errorFmt(reason))
            return [];
        }
    }

    async changePortStatus(deviceName: string, data: ChangePortStatusRequest) {
        try {
            const resp = await api.post<ChangePortStatusResponse>("/api/v1/devices/" + deviceName + "/port-status", data)
            return resp.data;
        } catch (reason: any) {
            errorToast("Не удалось изменить статус порта", errorFmt(reason))
            throw reason;
        }
    }

}

const devicesService = new DevicesService();
export default devicesService;
