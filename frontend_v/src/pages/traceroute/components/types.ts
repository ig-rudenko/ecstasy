export type TracerouteMode = "vlan" | "mac" | "neighbors";
export type TracerouteVisualizationMode = "graph" | "map";

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

export interface TracerouteMapNode {
    id: string;
    label: string;
    title?: string;
    lat: number;
    lon: number;
    device?: {
        name: string;
        ip: string;
        vendor: string;
        model: string;
        group: string;
        serial_number: string;
        os_version: string;
        url: string;
    } | null;
    inherited_from?: string;
    kind?: string;
}

export interface TracerouteMapEdge {
    from: string;
    to: string;
    title?: Record<string, unknown>;
    value?: number;
}

export interface TracerouteMapSkippedNode {
    id: string;
    label: string;
    reason: string;
}

export interface TracerouteMapData {
    nodes: TracerouteMapNode[];
    edges: TracerouteMapEdge[];
    skipped_nodes: TracerouteMapSkippedNode[];
    vlansInfo?: VlanCountInfo[];
}
