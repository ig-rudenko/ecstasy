class ZabbixInfo {
    constructor(
        public description: string,
        public inventory: Object,
    ) {}
}

class GeneralInfo {
    constructor(
        public coords: Array<string>,
        public deviceIP: string,
        public deviceName: string,
        public elasticStackLink: string,
        public permission: number,
        public zabbixHostID: number,
        public zabbixInfo: ZabbixInfo,
        public zabbixURL: string
    ) {}
}


function newZabbixInfo(data: any): ZabbixInfo {
    return new ZabbixInfo(data.description, data.inventory)
}

function newGeneralInfo(data: any): GeneralInfo {
    return new GeneralInfo(
        Array.from(data.coords),
        data.deviceIP,
        data.deviceName,
        data.elasticStackLink,
        data.permission,
        data.zabbixHostID,
        newZabbixInfo(data.zabbixInfo),
        data.zabbixURL,
    )
}

export {ZabbixInfo, GeneralInfo, newGeneralInfo}