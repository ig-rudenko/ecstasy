import {Device} from "@/services/devices";
import {errorToast} from "@/services/my.toast.ts";
import errorFmt from "@/errorFmt.ts";
import api from "@/services/api";


export interface InterfacesCount {
    abons: number;
    abons_down: number;
    abons_down_no_desc: number;
    abons_down_with_desc: number;
    abons_up: number;
    abons_up_no_desc: number;
    abons_up_with_desc: number;
    count: number;
}

export interface DeviceLink {
    deviceName: string;
    url: string;
}

export interface DeviceInterface {
    name: string;
    status: string;
    description: string;
    vlans: number[];
    comments: InterfaceComment[];
    graphsLink?: string;
    link?: DeviceLink;
}

export interface InterfaceComment {
    id: number;
    user: string;
    text: string;
    createdTime: string;
}

export interface InterfaceDescriptionMatchResult {
    device: string
    comments: InterfaceComment[]
    interface: {
        name: string
        status: string
        description: string
        vlans: string
        savedTime: string
        vlansSavedTime: string
    }
}

export function calculateInterfacesWorkload(devices: Device[]): number[] {
    let abonsUpWithDesc = 0;
    let abonsUpNoDesc = 0;
    let abonsDownWithDesc = 0;
    let abonsDownNoDesc = 0;
    let systems = 0;

    for (let dev of devices) {
        if (!dev.interfaces_count) continue;

        const i = dev.interfaces_count;

        abonsUpWithDesc += i.abons_up_with_desc;
        abonsUpNoDesc += i.abons_up_no_desc;
        abonsDownWithDesc += i.abons_down_with_desc;
        abonsDownNoDesc += i.abons_down_no_desc;
        systems += i.count - (i.abons_up_with_desc + i.abons_up_no_desc + i.abons_down_with_desc + i.abons_down_no_desc);
    }
    return [abonsUpWithDesc, abonsUpNoDesc, abonsDownWithDesc, abonsDownNoDesc, systems]
}


export async function findInterfacesByDescription(description: string): Promise<InterfaceDescriptionMatchResult[]> {
    const url = "/tools/api/find-by-desc?pattern=" + description;
    try {
        const resp = await api.get<{interfaces: InterfaceDescriptionMatchResult[]}>(url)
        return resp.data.interfaces;
    } catch (error: any) {
        console.error(error);
        errorToast("Не удалось найти интерфейсы по описанию", errorFmt(error))
        return [];
    }
}