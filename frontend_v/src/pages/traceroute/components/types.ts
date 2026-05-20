export type TracerouteMode = "vlan" | "mac" | "neighbors";

export interface VlanTracerouteOptions {
    adminDownPorts: boolean;
    showEmptyPorts: boolean;
    doubleCheckVlan: boolean;
    graphMinLength: number;
    deviceNameFilter: string;
    groupFilter: string;
    nodesOnly: boolean;
    maximized: boolean;
    rendered: boolean;
}

export interface MacTracerouteOptions {
    maximized: boolean;
    rendered: boolean;
    vlanFilter: number | null;
}

export interface TracerouteInput {
    vlan: number | null;
    mac: string;
}

export interface VlanCountInfo {
    vid: number;
    count: number;
    name: string;
    description: string;
}
