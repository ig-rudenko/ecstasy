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


export class DevicesService {


    async getDevicesList(): Promise<Device[]> {
        try {
            let resp = await api.get<Device[]>("/device/api/list_all");
            return resp.data;
        } catch (reason: any) {
            errorToast("Не удалось получить список устройств", errorFmt(reason))
            return [];
        }
    }

    async getDevicesListWithInterfacesWorkload(): Promise<Device[]> {
        try {
            let resp = await api.get<DevicesWithCount>("/device/api/workload/interfaces");
            return resp.data.devices;
        } catch (reason: any) {
            errorToast("Не удалось получить список устройств", errorFmt(reason))
            return [];
        }
    }

}

const devicesService = new DevicesService();
export default devicesService;
