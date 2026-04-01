import api from "@/services/api";
import errorFmt from "@/errorFmt";
import {Device} from "@/services/devices";
import {errorToast} from "@/services/my.toast";


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
    comments?: InterfaceComment[];
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


export async function findInterfacesByDescription(pattern: string, isRegex = false): Promise<InterfaceDescriptionMatchResult[]> {
    const url = "/api/v1/tools/find-by-desc";
    let params = {
        pattern: pattern,
        is_regex: isRegex ? "1" : "0"
    }
    try {
        const resp = await api.get<{ interfaces: InterfaceDescriptionMatchResult[] }>(url, {params})
        return resp.data.interfaces;
    } catch (error: any) {
        errorToast("Не удалось найти интерфейсы по описанию", errorFmt(error))
        return [];
    }
}

export function newInterface(data: any): DeviceInterface {
    let comments: InterfaceComment[] = []
    if (data.Comments) {  // old format
        comments = data.Comments
    } else if (data.comments) {  // new format
        comments = data.comments
    }

    let vlans: number[] = []
    if (data["VLAN's"]) {  // old format
        vlans = data["VLAN's"].map(Number)
    } else if (data["vlans"]) {  // new format
        vlans = data["vlans"].map(Number)
    }

    let link: DeviceLink | undefined = undefined;
    if (data.Link) {  // old format
        link = {deviceName: data.Link.device_name, url: data.Link.url}
    } else if (data.link) {  // new format
        link = {deviceName: data.link.deviceName, url: data.link.url}
    }

    return {
        name: data.Interface || data.name,
        status: data.Status || data.status,
        description: data.Description || data.description,
        vlans: vlans,
        comments: comments,
        graphsLink: data.GraphsLink || data.graphsLink,
        link: link,
    }
}

export function newInterfacesList(data: any[]): DeviceInterface[] {
    let res: DeviceInterface[] = []
    for (const line of data) {
        res.push(newInterface(line))
    }
    return res
}

function sameComments(left?: InterfaceComment[], right?: InterfaceComment[]): boolean {
    if (!left?.length && !right?.length) return true;
    if (!left || !right || left.length !== right.length) return false;

    for (let i = 0; i < left.length; i++) {
        if (
            left[i].id !== right[i].id ||
            left[i].user !== right[i].user ||
            left[i].text !== right[i].text ||
            left[i].createdTime !== right[i].createdTime
        ) {
            return false;
        }
    }

    return true;
}

function sameVlans(left: number[], right: number[]): boolean {
    if (left.length !== right.length) return false;
    for (let i = 0; i < left.length; i++) {
        if (left[i] !== right[i]) return false;
    }
    return true;
}

function sameLink(left?: DeviceLink, right?: DeviceLink): boolean {
    if (!left && !right) return true;
    if (!left || !right) return false;
    return left.deviceName === right.deviceName && left.url === right.url;
}

export function reconcileInterfacesList(current: DeviceInterface[], nextRaw: any[]): DeviceInterface[] {
    const currentByName = new Map(current.map((item) => [item.name, item]));
    const next = newInterfacesList(nextRaw);

    return next.map((item) => {
        const prev = currentByName.get(item.name);
        if (!prev) return item;

        const unchanged =
            prev.status === item.status &&
            prev.description === item.description &&
            prev.graphsLink === item.graphsLink &&
            sameVlans(prev.vlans, item.vlans) &&
            sameComments(prev.comments, item.comments) &&
            sameLink(prev.link, item.link);

        return unchanged ? prev : item;
    });
}
