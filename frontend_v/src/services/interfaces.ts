import {Device} from "@/services/devices";


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
