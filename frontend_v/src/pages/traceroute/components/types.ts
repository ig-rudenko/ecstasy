export type TracerouteMode = "vlan" | "mac" | "neighbors";
export type TracerouteVisualizationMode = "graph" | "map";
export type TrunkFilterMode = "off" | "mark_broad" | "hide_broad";

export interface VlanTracerouteOptions {
    adminDownPorts: boolean;
    showEmptyPorts: boolean;
    doubleCheckVlan: boolean;
    graphMinLength: number;
    trunkFilterMode: TrunkFilterMode;
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
    title?: EdgeTitlePayload;
    value?: number;
    color?: string | Record<string, unknown>;
    dashes?: boolean | number[];
}

export interface VlanMatchInfo {
    confidence?: "exact" | "high" | "normal" | "medium" | "low";
    exact_match?: boolean;
    src?: VlanPortMatchInfo;
    dst?: VlanPortMatchInfo | null;
}

export interface VlanPortMatchInfo {
    confidence?: string;
    broad_trunk?: boolean;
    exact_match?: boolean;
    vlan_count?: number;
    device_vlan_count?: number;
    largest_range_size?: number;
    reason?: string;
    matched_range?: {
        from: number;
        to: number;
    };
}

export interface EdgeTitlePayload {
    kind?: string;
    src?: {
        device?: string;
        port?: string;
    };
    dst?: {
        device?: string;
        port?: string;
    };
    destination_description?: string;
    vlan_match?: VlanMatchInfo;
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
