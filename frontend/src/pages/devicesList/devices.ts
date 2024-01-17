import {InterfacesCount, newInterfacesCount} from "../../types/interfaces";


class Device {
    constructor(
        public ip: string,
        public name: string,
        public model: string,
        public group: string,
        public vendor: string,
        public interfacesCount: InterfacesCount | null
    ) {}
}

function newDevicesList(data: Array<any>): Array<Device> {
    if (!data) return []
    let res: Array<Device> = []
    for (const elem of data) {
        res.push(
            new Device(
                elem.ip, elem.name, elem.model, elem.group, elem.vendor,
                elem.interfaces_count?newInterfacesCount(elem.interfaces_count):null
            )
        )
    }
    return res

}

export {Device, newDevicesList}