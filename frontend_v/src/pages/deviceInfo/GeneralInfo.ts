export interface ZabbixMapInfo {
    sysmapid: number,
    name: string,
}

export interface ZabbixInfo {
    description: string;
    inventory: any;
    monitoringAvailable: number;
    maps: ZabbixMapInfo[];
}

export interface GeneralInfo {
    coords: [string, string],
    deviceIP: string,
    deviceName: string,
    elasticStackLink: string,
    permission: number,
    zabbixHostID: number,
    zabbixInfo: ZabbixInfo,
    zabbixURL: string,
    consoleURL: string,
    uptime: number,
}
