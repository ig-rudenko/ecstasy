<template>
    <section
        class="relative overflow-hidden rounded-4xl border border-gray-200/80 bg-white/80 shadow-inner dark:border-gray-700/80 dark:bg-gray-900/45"
        :class="maximized ? 'traceroute-map--maximized' : ''"
    >
        <div
            class="absolute top-3 flex flex-col gap-2 sm:flex-row sm:items-center"
            style="left: 3.5rem; z-index: 1100; max-width: calc(100% - 9rem)"
        >
            <InputText
                v-model="search"
                placeholder="Найти узел"
                class="h-10 w-full rounded-xl! bg-white/95! font-mono! text-gray-900! dark:bg-gray-950/80! dark:text-gray-100! border-gray-200/80! dark:border-gray-700/60! sm:w-56!"
                @keyup.enter="highlightSearchMatches"
            />
            <Button
                icon="pi pi-search"
                rounded
                severity="secondary"
                v-tooltip.bottom="'Найти узел на карте'"
                @click="highlightSearchMatches"
            />
            <Button
                :icon="maximized ? 'pi pi-times' : 'pi pi-expand'"
                severity="secondary"
                rounded
                v-tooltip.bottom="maximized ? 'Выйти из полного экрана' : 'На весь экран'"
                @click="toggleMaximize"
            />
            <Button
                icon="pi pi-filter-slash"
                severity="secondary"
                rounded
                v-tooltip.bottom="'Сбросить подсветку'"
                @click="resetHighlights"
            />
            <Button
                :icon="clusterPorts ? 'pi pi-sitemap' : 'pi pi-circle'"
                :severity="clusterPorts ? 'primary' : 'secondary'"
                rounded
                v-tooltip.bottom="clusterPorts ? 'Отключить кластеры портов' : 'Показать порты кластерами'"
                @click="togglePortClusters"
            />
        </div>

        <div
            ref="mapElement"
            class="h-150 min-h-120 w-full bg-slate-950 sm:h-225"
            :class="maximized ? 'traceroute-map__canvas--maximized' : ''"
        />

        <div
            v-if="data.skipped_nodes.length || inheritedNodesCount"
            class="border-t border-gray-200/80 bg-white/90 p-3 text-sm text-gray-600 dark:border-gray-700/80 dark:bg-gray-900/80 dark:text-gray-300"
        >
            <div>
                На карте показано {{ data.nodes.length }} узлов, включая {{ inheritedNodesCount }} узлов с координатами,
                унаследованными от соседнего оборудования.
            </div>
            <div v-if="data.skipped_nodes.length" class="mt-2">
                <div class="font-medium text-gray-800 dark:text-gray-100">
                    Не удалось отобразить {{ data.skipped_nodes.length }} узлов:
                </div>
                <ul class="mt-2 grid max-h-40 gap-1 overflow-y-auto rounded-xl bg-gray-50/80 p-2 dark:bg-gray-950/40">
                    <li
                        v-for="node in data.skipped_nodes"
                        :key="node.id"
                        class="flex min-w-0 flex-col gap-0.5 rounded-lg px-2 py-1 sm:flex-row sm:items-center sm:justify-between"
                    >
                        <span class="min-w-0 truncate font-mono text-gray-900 dark:text-gray-100">
                            {{ node.label || node.id }}
                        </span>
                        <span class="text-xs text-gray-500 dark:text-gray-400">
                            {{ getSkippedReasonLabel(node.reason) }}
                        </span>
                    </li>
                </ul>
            </div>
        </div>
    </section>
</template>

<script setup lang="ts">
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import "leaflet.markercluster/dist/MarkerCluster.css";

import {
    circleMarker,
    Control,
    divIcon,
    featureGroup,
    latLngBounds,
    Map as LMap,
    polyline,
    tileLayer,
    type CircleMarker,
    type FeatureGroup,
    type LatLngExpression,
    type MarkerClusterGroup,
    type Marker,
    type Polyline,
    type TileLayer,
} from "leaflet";
import * as Leaflet from "leaflet";
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import api from "@/services/api";
import type { TracerouteMapData, TracerouteMapEdge, TracerouteMapNode } from "./types";
import {
    createEdgePopup,
    createEdgeTooltip,
    createNodePopup,
    getEdgeEndpoints,
    type LoadedInterfaceInfo,
} from "./mapHelpers";

const props = defineProps<{
    data: TracerouteMapData;
}>();

const mapElement = ref<HTMLElement | null>(null);
const search = ref("");
const maximized = ref(false);
const clusterPorts = ref(false);
let map: LMap | null = null;
let nodesLayer: FeatureGroup<CircleMarker> | null = null;
let suspiciousNodesLayer: FeatureGroup<CircleMarker> | null = null;
let portsLayer: FeatureGroup<CircleMarker | Marker> | null = null;
let portClusterLayer: MarkerClusterGroup | null = null;
let edgesLayer: FeatureGroup<Polyline> | null = null;
let suspiciousEdgesLayer: FeatureGroup<Polyline> | null = null;
let layersControl: Control.Layers | null = null;
let resizeObserver: ResizeObserver | null = null;
let refreshAnimationFrame: number | null = null;
let markerClusterLoading: Promise<void> | null = null;
const markersById = new Map<string, CircleMarker>();
const markerDefaultStyles = new Map<string, MarkerStyle>();
const edgeDefaultStyles = new WeakMap<Polyline, EdgeStyle>();
const edgeLinesByNode = new Map<string, Polyline[]>();
const foundNodeIds = ref(new Set<string>());
const highlightedNodeId = ref<string | null>(null);
const PORT_CLUSTER_AUTO_THRESHOLD = 25;
const CLOSE_DEVICE_DISTANCE_METERS = 14;
const DEVICE_OFFSET_RADIUS_METERS = 14;
const DEVICE_OFFSET_RING_STEP_METERS = 8;
const PORT_OFFSET_RADIUS_METERS = 25;
const PORT_OFFSET_RING_STEP_METERS = 9;
const RADIAL_POINTS_PER_RING = 8;
const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));
const defaultMarkerStyle = {
    radius: 7,
    color: "#e0f2fe",
    weight: 2,
    fillColor: "#2563eb",
    fillOpacity: 0.9,
};
const highlightedMarkerStyle = {
    radius: 10,
    color: "#fef3c7",
    weight: 3,
    fillColor: "#f97316",
    fillOpacity: 1,
};
const suspiciousMarkerStyle = {
    radius: 7,
    color: "#e0f2fe",
    weight: 2,
    opacity: 0.35,
    fillColor: "#2563eb",
    fillOpacity: 0.35,
};
const inheritedNodesCount = computed(() => props.data.nodes.filter((node) => node.inherited_from).length);
const shouldAutoClusterPorts = computed(() => inheritedNodesCount.value >= PORT_CLUSTER_AUTO_THRESHOLD);

/**
 * Initializes Leaflet map instance.
 */
function initMap(): void {
    if (map || !mapElement.value) {
        return;
    }

    const tiles = createMapTiles();
    map = new LMap(mapElement.value, {
        layers: [tiles.osm],
        minZoom: 3,
    });
    map.createPane("tracerouteEdges");
    map.createPane("tracerouteSuspiciousEdges");
    map.createPane("tracerouteNodes");
    map.createPane("tracerouteSuspiciousNodes");
    map.createPane("traceroutePorts");
    map.getPane("tracerouteEdges")!.style.zIndex = "410";
    map.getPane("tracerouteSuspiciousEdges")!.style.zIndex = "411";
    map.getPane("tracerouteNodes")!.style.zIndex = "430";
    map.getPane("tracerouteSuspiciousNodes")!.style.zIndex = "435";
    map.getPane("traceroutePorts")!.style.zIndex = "440";
    map.setView([44.6, 33.5], 12);
    map.attributionControl.getContainer()?.remove();
    map.addControl(new Control.Scale());
    edgesLayer = featureGroup<Polyline>().addTo(map);
    suspiciousEdgesLayer = featureGroup<Polyline>().addTo(map);
    nodesLayer = featureGroup<CircleMarker>().addTo(map);
    suspiciousNodesLayer = featureGroup<CircleMarker>().addTo(map);
    portsLayer = featureGroup<CircleMarker | Marker>().addTo(map);
    portClusterLayer = clusterPorts.value ? createPortClusterLayer() : null;
    layersControl = new Control.Layers(
        {
            OSM: tiles.osm,
            Google: tiles.geoGoogle,
            ArcGIS: tiles.arcgisonline,
        },
        {
            Узлы: nodesLayer,
            "Сомнительные узлы/порты": suspiciousNodesLayer,
            Порты: portClusterLayer || portsLayer,
            Связи: edgesLayer,
            "Сомнительные связи": suspiciousEdgesLayer,
        }
    ).addTo(map);
    if (portClusterLayer) {
        portClusterLayer.addTo(map);
    }
}

/**
 * Creates fresh tile layer instances for a Leaflet map instance.
 */
function createMapTiles(): { geoGoogle: TileLayer; arcgisonline: TileLayer; osm: TileLayer } {
    const geoGoogle = tileLayer("https://www.google.com/maps/vt?lyrs=s@189&gl=cn&x={x}&y={y}&z={z}", {
        attribution: "google",
    });
    const arcgisonline = tileLayer(
        "http://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    );
    const osm = tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png");
    return { geoGoogle, arcgisonline, osm };
}

/**
 * Renders nodes and edges on the Leaflet map.
 */
function renderMap(shouldFitBounds = true): void {
    initMap();
    if (!map || !nodesLayer || !suspiciousNodesLayer || !portsLayer || !edgesLayer || !suspiciousEdgesLayer) {
        return;
    }

    nodesLayer.clearLayers();
    suspiciousNodesLayer.clearLayers();
    portsLayer.clearLayers();
    portClusterLayer?.clearLayers();
    edgesLayer.clearLayers();
    suspiciousEdgesLayer.clearLayers();
    markersById.clear();
    markerDefaultStyles.clear();
    edgeLinesByNode.clear();
    highlightedNodeId.value = null;

    const displayNodes = buildDisplayNodes(props.data.nodes);
    const nodesById = new Map<string, TracerouteMapNode>();
    for (const node of displayNodes) {
        nodesById.set(node.id, node);
    }

    for (const edge of props.data.edges) {
        const source = nodesById.get(edge.from);
        const target = nodesById.get(edge.to);
        if (!source || !target) {
            continue;
        }
        const edgeStyle = getDefaultEdgeStyle(edge);
        const line = polyline(createCurvedLinePoints(source, target), {
            pane: isSuspiciousEdge(edge) ? "tracerouteSuspiciousEdges" : "tracerouteEdges",
            ...edgeStyle,
        });
        edgeDefaultStyles.set(line, edgeStyle);
        line.bindTooltip(createEdgeTooltip(edge, source, target), { sticky: true });
        line.bindPopup(createEdgePopup(edge, null, false));
        line.on("click", () => {
            selectEdgeLine(line, edge);
            loadEdgeInterfaceInfo(edge, line);
        });
        line.addTo(isSuspiciousEdge(edge) ? suspiciousEdgesLayer : edgesLayer);
        addEdgeLineForNode(edge.from, line);
        addEdgeLineForNode(edge.to, line);
    }

    const deviceNodes: TracerouteMapNode[] = [];
    const portNodes: TracerouteMapNode[] = [];
    const suspiciousNodeIds = getSuspiciousNodeIds(nodesById);
    for (const node of displayNodes) {
        if (node.inherited_from) {
            portNodes.push(node);
            continue;
        }
        deviceNodes.push(node);
    }

    for (const node of deviceNodes) {
        if (suspiciousNodeIds.has(node.id)) {
            addNodeMarker(node, suspiciousNodesLayer, suspiciousMarkerStyle, "tracerouteSuspiciousNodes");
            continue;
        }
        addNodeMarker(node, nodesLayer, defaultMarkerStyle, "tracerouteNodes");
    }

    if (clusterPorts.value) {
        renderClusteredPorts(portNodes.filter((node) => !suspiciousNodeIds.has(node.id)));
    } else {
        for (const node of portNodes) {
            if (suspiciousNodeIds.has(node.id)) {
                continue;
            }
            addNodeMarker(node, portsLayer, getPortMarkerStyle(), "traceroutePorts");
        }
    }
    for (const node of portNodes) {
        if (suspiciousNodeIds.has(node.id)) {
            addNodeMarker(node, suspiciousNodesLayer, getSuspiciousPortMarkerStyle(), "tracerouteSuspiciousNodes");
        }
    }
    applySearchHighlight();

    const points = displayNodes.map((node) => [node.lat, node.lon] as LatLngExpression);
    if (shouldFitBounds && points.length) {
        map.fitBounds(latLngBounds(points), { padding: [40, 40], maxZoom: 17 });
    }
    refreshMapLayout();
}

/**
 * Builds display-only coordinates for overlapping equipment and inherited port nodes.
 */
function buildDisplayNodes(nodes: TracerouteMapNode[]): TracerouteMapNode[] {
    if (!map) {
        return nodes;
    }

    const deviceNodes = nodes.filter((node) => !node.inherited_from);
    const portNodes = nodes.filter((node) => node.inherited_from);
    const displayNodesById = new Map<string, TracerouteMapNode>();

    for (const group of groupCloseDeviceNodes(deviceNodes)) {
        const center = getGroupCenter(group.nodes);
        if (group.nodes.length === 1) {
            const node = group.nodes[0];
            displayNodesById.set(node.id, { ...node });
            continue;
        }
        group.nodes.forEach((node, index) => {
            const [lat, lon] = offsetCoordinate(
                center.lat,
                center.lon,
                getRadialRadius(index, DEVICE_OFFSET_RADIUS_METERS, DEVICE_OFFSET_RING_STEP_METERS),
                getRadialAngle(index)
            );
            displayNodesById.set(node.id, { ...node, lat, lon });
        });
    }

    const portsByParent = new Map<string, TracerouteMapNode[]>();
    for (const port of portNodes) {
        const parentId = port.inherited_from || "";
        const ports = portsByParent.get(parentId) || [];
        ports.push(port);
        portsByParent.set(parentId, ports);
    }

    for (const [parentId, ports] of portsByParent) {
        const parentNode = displayNodesById.get(parentId);
        ports.forEach((port, index) => {
            if (!parentNode) {
                displayNodesById.set(port.id, { ...port });
                return;
            }
            const [lat, lon] = offsetCoordinate(
                parentNode.lat,
                parentNode.lon,
                getRadialRadius(index, PORT_OFFSET_RADIUS_METERS, PORT_OFFSET_RING_STEP_METERS),
                getRadialAngle(index)
            );
            displayNodesById.set(port.id, { ...port, lat, lon });
        });
    }

    return nodes.map((node) => displayNodesById.get(node.id) || node);
}

/**
 * Groups equipment nodes whose coordinates are too close for readable markers.
 */
function groupCloseDeviceNodes(nodes: TracerouteMapNode[]): { nodes: TracerouteMapNode[] }[] {
    if (!map) {
        return nodes.map((node) => ({ nodes: [node] }));
    }
    const groups: { nodes: TracerouteMapNode[]; center: { lat: number; lon: number } }[] = [];
    for (const node of nodes) {
        const group = groups.find((item) => {
            const distance =
                map?.distance([node.lat, node.lon], [item.center.lat, item.center.lon]) ?? Number.MAX_VALUE;
            return distance <= CLOSE_DEVICE_DISTANCE_METERS;
        });
        if (!group) {
            groups.push({ nodes: [node], center: { lat: node.lat, lon: node.lon } });
            continue;
        }
        group.nodes.push(node);
        group.center = getGroupCenter(group.nodes);
    }
    return groups;
}

/**
 * Returns geographic center for a node group.
 */
function getGroupCenter(nodes: TracerouteMapNode[]): { lat: number; lon: number } {
    return {
        lat: nodes.reduce((sum, node) => sum + node.lat, 0) / nodes.length,
        lon: nodes.reduce((sum, node) => sum + node.lon, 0) / nodes.length,
    };
}

/**
 * Returns radial offset angle for a marker index.
 */
function getRadialAngle(index: number): number {
    return index * GOLDEN_ANGLE;
}

/**
 * Returns radial offset radius for a marker index.
 */
function getRadialRadius(index: number, baseRadius: number, ringStep: number): number {
    return baseRadius + Math.floor(index / RADIAL_POINTS_PER_RING) * ringStep;
}

/**
 * Offsets latitude and longitude by meters and angle.
 */
function offsetCoordinate(lat: number, lon: number, radiusMeters: number, angle: number): [number, number] {
    const earthRadius = 6378137;
    const northMeters = Math.sin(angle) * radiusMeters;
    const eastMeters = Math.cos(angle) * radiusMeters;
    const nextLat = lat + (northMeters / earthRadius) * (180 / Math.PI);
    const nextLon = lon + (eastMeters / (earthRadius * Math.cos((lat * Math.PI) / 180))) * (180 / Math.PI);
    return [nextLat, nextLon];
}

/**
 * Creates Leaflet.MarkerCluster layer for inherited ports.
 */
function createPortClusterLayer(): MarkerClusterGroup {
    return getMarkerClusterGroupFactory()({
        chunkedLoading: true,
        clusterPane: "traceroutePorts",
        disableClusteringAtZoom: 18,
        maxClusterRadius: 36,
        removeOutsideVisibleBounds: true,
        showCoverageOnHover: false,
        spiderfyOnMaxZoom: true,
        zoomToBoundsOnClick: true,
        spiderLegPolylineOptions: {
            color: "#f59e0b",
            opacity: 0.75,
            weight: 1.2,
        },
        iconCreateFunction: (cluster) =>
            divIcon({
                className: "traceroute-map-port-cluster",
                html: `<span>${cluster.getChildCount()}</span>`,
                iconSize: [34, 34],
                iconAnchor: [17, 17],
            }),
    });
}

/**
 * Adds a node or port marker to a target Leaflet layer.
 */
function addNodeMarker(
    node: TracerouteMapNode,
    targetLayer: FeatureGroup<CircleMarker | Marker> | FeatureGroup<CircleMarker>,
    markerStyle: MarkerStyle,
    pane: string
): CircleMarker {
    const mapMarker = circleMarker([node.lat, node.lon], {
        ...markerStyle,
        pane,
    });
    mapMarker.bindTooltip(node.label, { direction: "top", sticky: true });
    mapMarker.bindPopup(createNodePopup(node));
    mapMarker.on("click", () => highlightNodeEdges(node.id));
    mapMarker.addTo(targetLayer);
    mapMarker.bringToFront();
    markersById.set(node.id, mapMarker);
    markerDefaultStyles.set(node.id, markerStyle);
    return mapMarker;
}

/**
 * Renders inherited port nodes through Leaflet.MarkerCluster.
 */
function renderClusteredPorts(portNodes: TracerouteMapNode[]): void {
    if (!portClusterLayer) {
        return;
    }
    for (const node of portNodes) {
        addNodeMarker(node, portClusterLayer, getPortMarkerStyle(), "traceroutePorts");
    }
}

/**
 * Returns default inherited port marker style.
 */
function getPortMarkerStyle(): typeof defaultMarkerStyle {
    return {
        radius: 5,
        color: "#fde68a",
        weight: 2,
        fillColor: "#f59e0b",
        fillOpacity: 0.95,
    };
}

/**
 * Returns inherited port marker style for ports connected only through suspicious edges.
 */
function getSuspiciousPortMarkerStyle(): MarkerStyle {
    return {
        radius: 5,
        color: "#fde68a",
        weight: 2,
        opacity: 0.5,
        fillColor: "#f59e0b",
        fillOpacity: 0.5,
    };
}

/**
 * Returns nodes whose every rendered edge is suspicious.
 */
function getSuspiciousNodeIds(nodesById: Map<string, TracerouteMapNode>): Set<string> {
    const totalEdgesByNode = new Map<string, number>();
    const suspiciousEdgesByNode = new Map<string, number>();
    const portNodeIdsByEndpoint = getPortNodeIdsByEndpoint(nodesById);

    for (const edge of props.data.edges) {
        const source = nodesById.get(edge.from);
        const target = nodesById.get(edge.to);
        if (!source || !target) {
            continue;
        }

        const isSuspicious = isSuspiciousEdge(edge);
        const edgeNodeIds = new Set([source.id, target.id, ...getEdgePortNodeIds(edge, portNodeIdsByEndpoint)]);
        for (const nodeId of edgeNodeIds) {
            totalEdgesByNode.set(nodeId, (totalEdgesByNode.get(nodeId) || 0) + 1);
            if (isSuspicious) {
                suspiciousEdgesByNode.set(nodeId, (suspiciousEdgesByNode.get(nodeId) || 0) + 1);
            }
        }
    }

    return new Set(
        [...totalEdgesByNode.entries()]
            .filter(([nodeId, total]) => total > 0 && (suspiciousEdgesByNode.get(nodeId) || 0) === total)
            .map(([nodeId]) => nodeId)
    );
}

/**
 * Builds an index for inherited port nodes by device and port name.
 */
function getPortNodeIdsByEndpoint(nodesById: Map<string, TracerouteMapNode>): Map<string, string[]> {
    const portNodeIdsByEndpoint = new Map<string, string[]>();
    for (const node of nodesById.values()) {
        if (!node.inherited_from) {
            continue;
        }
        const port = extractPortNameFromNode(node);
        if (!port) {
            continue;
        }
        const key = getEndpointKey(node.inherited_from, port);
        portNodeIdsByEndpoint.set(key, [...(portNodeIdsByEndpoint.get(key) || []), node.id]);
    }
    return portNodeIdsByEndpoint;
}

/**
 * Returns inherited port node ids referenced by an edge title payload.
 */
function getEdgePortNodeIds(edge: TracerouteMapEdge, portNodeIdsByEndpoint: Map<string, string[]>): string[] {
    const endpoints = [edge.title?.src, edge.title?.dst];
    return endpoints.flatMap((endpoint) => {
        if (!endpoint?.device || !endpoint.port) {
            return [];
        }
        return portNodeIdsByEndpoint.get(getEndpointKey(endpoint.device, endpoint.port)) || [];
    });
}

/**
 * Returns stable endpoint key for device and port lookup.
 */
function getEndpointKey(device: string, port: string): string {
    return `${device.trim().toLowerCase()}\u0000${port.trim().toLowerCase()}`;
}

/**
 * Extracts port name from inherited node id or label.
 */
function extractPortNameFromNode(node: TracerouteMapNode): string {
    const sources = [node.id, node.label];
    for (const value of sources) {
        const match = String(value).match(/\bp:\((.*)\)$/i);
        if (match?.[1]) {
            return match[1].trim();
        }
    }
    return "";
}

/**
 * Checks whether an edge has low or medium confidence.
 */
function isSuspiciousEdge(edge: TracerouteMapEdge): boolean {
    const confidence = edge.title?.vlan_match?.confidence;
    return confidence === "low" || confidence === "medium";
}

/**
 * Adds a rendered edge line to the node index.
 */
function addEdgeLineForNode(nodeId: string, line: Polyline): void {
    const lines = edgeLinesByNode.get(nodeId) || [];
    lines.push(line);
    edgeLinesByNode.set(nodeId, lines);
}

/**
 * Highlights nodes matching current search query without moving the map.
 */
function highlightSearchMatches(): void {
    const query = search.value.trim().toLowerCase();
    if (!query) {
        foundNodeIds.value = new Set<string>();
        applySearchHighlight();
        return;
    }

    foundNodeIds.value = new Set(
        props.data.nodes
            .filter((item) => item.id.toLowerCase().includes(query) || item.label.toLowerCase().includes(query))
            .map((item) => item.id)
    );
    applySearchHighlight();
}

/**
 * Applies visual marker state for search results.
 */
function applySearchHighlight(): void {
    for (const [nodeId, marker] of markersById) {
        const node = props.data.nodes.find((item) => item.id === nodeId);
        marker.setStyle(
            foundNodeIds.value.has(nodeId)
                ? highlightedMarkerStyle
                : markerDefaultStyles.get(nodeId) || (node?.inherited_from ? getPortMarkerStyle() : defaultMarkerStyle)
        );
        marker.bringToFront();
    }
}

/**
 * Highlights all edge lines connected to a node.
 */
function highlightNodeEdges(nodeId: string): void {
    resetEdgeHighlights();
    highlightedNodeId.value = nodeId;
    for (const line of edgeLinesByNode.get(nodeId) || []) {
        line.setStyle({
            color: "#22c55e",
            opacity: 0.95,
            weight: Math.max(3, (edgeDefaultStyles.get(line)?.weight || 1) + 1),
        });
        line.bringToFront();
    }
}

/**
 * Clears search results, selected edge and node edge highlights.
 */
function resetHighlights(): void {
    search.value = "";
    foundNodeIds.value = new Set<string>();
    applySearchHighlight();
    resetEdgeHighlights();
}

/**
 * Toggles inherited port clustering.
 */
async function togglePortClusters(): Promise<void> {
    clusterPorts.value = !clusterPorts.value;
    if (clusterPorts.value) {
        await ensureMarkerClusterLoaded();
    }
    rebuildMap(false);
}

/**
 * Loads Leaflet.MarkerCluster after exposing Leaflet as global L for its UMD bundle.
 */
async function ensureMarkerClusterLoaded(): Promise<void> {
    if (getMarkerClusterGroupFactoryOrNull()) {
        return;
    }
    if (!markerClusterLoading) {
        window.L = Leaflet;
        markerClusterLoading = import("leaflet.markercluster").then(() => undefined);
    }
    await markerClusterLoading;
}

/**
 * Returns loaded marker cluster factory.
 */
function getMarkerClusterGroupFactory(): typeof Leaflet.markerClusterGroup {
    const factory = getMarkerClusterGroupFactoryOrNull();
    if (!factory) {
        throw new Error("Leaflet.MarkerCluster is not loaded.");
    }
    return factory;
}

/**
 * Returns marker cluster factory without relying on static type augmentation.
 */
function getMarkerClusterGroupFactoryOrNull(): typeof Leaflet.markerClusterGroup | null {
    return (
        (
            Leaflet as unknown as {
                markerClusterGroup?: typeof Leaflet.markerClusterGroup;
            }
        ).markerClusterGroup ?? null
    );
}

/**
 * Restores default style for all highlighted edge lines.
 */
function resetEdgeHighlights(): void {
    highlightedNodeId.value = null;
    for (const lines of edgeLinesByNode.values()) {
        for (const line of lines) {
            const defaultStyle = edgeDefaultStyles.get(line);
            if (defaultStyle) {
                line.setStyle(defaultStyle);
            }
        }
    }
}

/**
 * Toggles fullscreen-like map layout.
 */
function toggleMaximize(): void {
    maximized.value = !maximized.value;
    document.body.classList.toggle("overflow-hidden", maximized.value);
    document.documentElement.classList.toggle("overflow-hidden", maximized.value);
    rebuildMap();
}

/**
 * Recreates Leaflet after switching fullscreen layout.
 */
function rebuildMap(shouldFitBounds = true): void {
    destroyMap();
    nextTick(() => {
        renderMap(shouldFitBounds);
    });
}

/**
 * Refreshes Leaflet size and tile layers after layout changes.
 */
function refreshMapLayout(): void {
    nextTick(() => {
        if (refreshAnimationFrame !== null) {
            window.cancelAnimationFrame(refreshAnimationFrame);
        }
        refreshAnimationFrame = window.requestAnimationFrame(() => {
            map?.invalidateSize({ pan: false });
            refreshAnimationFrame = null;
        });
    });
}

/**
 * Selects an edge line and updates its visual style.
 */
function selectEdgeLine(line: Polyline, edge: TracerouteMapEdge): void {
    resetEdgeHighlights();
    line.setStyle({
        color: "#f97316",
        opacity: 0.95,
        weight: Math.max(3, Math.min(Number(edge.value || 2) + 1, 5)),
    });
    line.bringToFront();
}

/**
 * Returns user-facing skipped node reason.
 */
function getSkippedReasonLabel(reason: string): string {
    const labels: Record<string, string> = {
        invalid_zabbix_coordinates: "некорректные координаты",
        no_zabbix_coordinates: "нет координат и соседнего устройства",
    };
    return labels[reason] || reason;
}

interface EdgeStyle {
    color: string;
    opacity: number;
    weight: number;
    dashArray?: string;
}

type MarkerStyle = typeof defaultMarkerStyle & {
    dashArray?: string;
    opacity?: number;
};

/**
 * Returns default edge style.
 */
function getDefaultEdgeStyle(edge: TracerouteMapEdge): EdgeStyle {
    const confidence = edge.title?.vlan_match?.confidence;
    if (confidence === "low") {
        return {
            color: "#94a3b8",
            opacity: 0.38,
            weight: Math.max(2, Math.min(Number(edge.value || 1) + 1, 3)),
            dashArray: "6 5",
        };
    }
    if (confidence === "medium") {
        return {
            color: "#f59e0b",
            opacity: 0.3,
            weight: Math.max(2, Math.min(Number(edge.value || 1) + 1, 3.5)),
            dashArray: "8 4",
        };
    }
    return {
        color: "#38bdf8",
        opacity: 0.65,
        weight: Math.max(2, Math.min(Number(edge.value || 1) + 1, 4)),
    };
}

/**
 * Builds a slightly curved line using quadratic Bezier interpolation.
 */
function createCurvedLinePoints(source: TracerouteMapNode, target: TracerouteMapNode): LatLngExpression[] {
    const start = { lat: source.lat, lon: source.lon };
    const end = { lat: target.lat, lon: target.lon };
    const deltaLat = end.lat - start.lat;
    const deltaLon = end.lon - start.lon;
    const distance = Math.sqrt(deltaLat * deltaLat + deltaLon * deltaLon) || 0.0001;
    const curveOffset = Math.max(distance * 0.14, 0.00005);
    const control = {
        lat: (start.lat + end.lat) / 2 - (deltaLon / distance) * curveOffset,
        lon: (start.lon + end.lon) / 2 + (deltaLat / distance) * curveOffset,
    };

    const points: LatLngExpression[] = [];
    for (let index = 0; index <= 16; index += 1) {
        const t = index / 16;
        const oneMinusT = 1 - t;
        points.push([
            oneMinusT * oneMinusT * start.lat + 2 * oneMinusT * t * control.lat + t * t * end.lat,
            oneMinusT * oneMinusT * start.lon + 2 * oneMinusT * t * control.lon + t * t * end.lon,
        ]);
    }
    return points;
}

/**
 * Loads historical interface VLAN info for ports mentioned in an edge.
 */
async function loadEdgeInterfaceInfo(edge: TracerouteMapEdge, line: Polyline): Promise<void> {
    line.setPopupContent(createEdgePopup(edge, null, true));
    const endpoints = getEdgeEndpoints(edge);
    const loaded: LoadedInterfaceInfo[] = [];

    for (const endpoint of endpoints) {
        if (!endpoint.device || !endpoint.port) {
            continue;
        }
        const info = await fetchInterfaceInfo(endpoint.device, endpoint.port);
        if (info) {
            loaded.push(info);
        }
    }

    line.setPopupContent(createEdgePopup(edge, loaded, false));
    line.openPopup();
}

/**
 * Fetches historical VLAN/status info for a single interface.
 */
async function fetchInterfaceInfo(device: string, port: string): Promise<LoadedInterfaceInfo | null> {
    try {
        const response = await api.get(`/api/v1/devices/${encodeURIComponent(device)}/interfaces`, {
            params: {
                current_status: 0,
                vlans: 1,
                add_links: 0,
                add_comments: 0,
                add_zabbix_graph: 0,
            },
        });
        const item = response.data.interfaces?.find((iface: { name?: string }) => iface.name === port);
        if (!item) {
            return {
                device,
                port,
                status: "не найден",
                vlans: [],
                collected: response.data.collected || "",
            };
        }
        return {
            device,
            port,
            status: String(item.status || ""),
            vlans: Array.isArray(item.vlans) ? item.vlans.map(Number) : [],
            collected: response.data.collected || "",
        };
    } catch {
        return {
            device,
            port,
            status: "ошибка загрузки",
            vlans: [],
            collected: "",
        };
    }
}

watch(
    () => props.data,
    async () => {
        if (shouldAutoClusterPorts.value && !clusterPorts.value) {
            clusterPorts.value = true;
            await ensureMarkerClusterLoaded();
        }
        nextTick(renderMap);
    },
    { deep: true, immediate: true }
);

watch(search, (value) => {
    if (!value.trim()) {
        highlightSearchMatches();
    }
});

onMounted(() => {
    if (!mapElement.value) {
        return;
    }
    resizeObserver = new ResizeObserver(() => refreshMapLayout());
    resizeObserver.observe(mapElement.value);
});

onBeforeUnmount(() => {
    document.body.classList.remove("overflow-hidden");
    document.documentElement.classList.remove("overflow-hidden");
    resizeObserver?.disconnect();
    resizeObserver = null;
    destroyMap();
});

/**
 * Destroys current Leaflet instance and clears the map container.
 */
function destroyMap(): void {
    if (refreshAnimationFrame !== null) {
        window.cancelAnimationFrame(refreshAnimationFrame);
        refreshAnimationFrame = null;
    }
    layersControl?.remove();
    map?.remove();
    if (mapElement.value) {
        mapElement.value.innerHTML = "";
    }
    map = null;
    nodesLayer = null;
    suspiciousNodesLayer = null;
    portsLayer = null;
    portClusterLayer = null;
    edgesLayer = null;
    suspiciousEdgesLayer = null;
    layersControl = null;
    markersById.clear();
    markerDefaultStyles.clear();
}
</script>

<style scoped>
.traceroute-map--maximized {
    position: fixed !important;
    inset: 0 !important;
    z-index: 10000 !important;
    width: 100vw !important;
    height: 100dvh !important;
    border: 0 !important;
    border-radius: 0 !important;
    background: #020617 !important;
}

.traceroute-map__canvas--maximized {
    width: 100vw !important;
    height: 100dvh !important;
    min-height: 100dvh !important;
}

:deep(.leaflet-interactive:focus),
:deep(.leaflet-interactive:focus-visible),
:deep(path.leaflet-interactive:focus),
:deep(path.leaflet-interactive:focus-visible) {
    outline: none;
}

:deep(.traceroute-map-popup) {
    min-width: 220px;
    max-width: min(28rem, 78vw);
    color: #0f172a;
}

:deep(.traceroute-map-popup__title) {
    margin-bottom: 0.45rem;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    font-size: 0.9rem;
    font-weight: 700;
}

:deep(.traceroute-map-popup__muted) {
    color: #64748b;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    font-size: 0.75rem;
}

:deep(.traceroute-map-popup__hint) {
    margin-top: 0.45rem;
    color: #92400e;
    font-size: 0.72rem;
}

:deep(.traceroute-map-popup__grid) {
    display: grid;
    grid-template-columns: max-content minmax(0, 1fr);
    gap: 0.2rem 0.65rem;
    align-items: start;
}

:deep(.traceroute-map-popup__label) {
    color: #64748b;
    font-size: 0.72rem;
}

:deep(.traceroute-map-popup__value) {
    overflow-wrap: anywhere;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    font-size: 0.75rem;
}

:deep(.traceroute-map-popup__link) {
    display: inline-flex;
    margin-top: 0.65rem;
    color: #2563eb;
    font-size: 0.8rem;
    font-weight: 600;
}

:deep(.traceroute-map-edge-tooltip) {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    font-size: 0.75rem;
}

:deep(.traceroute-map-popup__interfaces) {
    gap: 0.45rem;
    margin-top: 0.65rem;
}

:deep(.traceroute-map-popup__interface) {
    border-top: 1px solid #e2e8f0;
    padding-top: 0.45rem;
}

:deep(.traceroute-map-popup__interface-head) {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 0.75rem;
}

:deep(.traceroute-map-popup__status) {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 2.6rem;
    border-radius: 999px;
    padding: 0.12rem 0.5rem;
    font-size: 0.68rem;
    font-weight: 700;
    line-height: 1.2;
    white-space: nowrap;
}

:deep(.traceroute-map-popup__status--up) {
    background: #dcfce7;
    color: #166534;
}

:deep(.traceroute-map-popup__status--down) {
    background: #fee2e2;
    color: #991b1b;
}

:deep(.traceroute-map-popup__status--error) {
    background: #ffedd5;
    color: #9a3412;
}

:deep(.traceroute-map-popup__status--unknown) {
    background: #e2e8f0;
    color: #334155;
}

:deep(.traceroute-map-popup__confidence) {
    display: inline-flex;
    max-width: 100%;
    border-radius: 999px;
    padding: 0.12rem 0.5rem;
    font-size: 0.68rem;
    font-weight: 700;
    line-height: 1.2;
}

:deep(.traceroute-map-popup__confidence--low) {
    background: #fee2e2;
    color: #991b1b;
}

:deep(.traceroute-map-popup__confidence--medium) {
    background: #fef3c7;
    color: #92400e;
}

:deep(.traceroute-map-popup__vlan-block) {
    display: grid;
    grid-template-columns: max-content minmax(0, 1fr);
    gap: 0.35rem;
    margin-top: 0.4rem;
    align-items: start;
}

:deep(.traceroute-map-popup__vlan-list) {
    text-align: justify;
    overflow: auto;
    overflow-wrap: anywhere;
    border-radius: 0.45rem;
    background: #f8fafc;
    padding: 0.25rem 0.35rem;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    font-size: 0.72rem;
    line-height: 1.35;
}

:deep(.traceroute-map-port-cluster) {
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid #fef3c7;
    border-radius: 999px;
    background: #f59e0b;
    color: #111827;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    font-size: 0.8rem;
    font-weight: 800;
    box-shadow: 0 8px 18px rgba(15, 23, 42, 0.32);
}

:deep(.traceroute-map-port-cluster span) {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 1.25rem;
    height: 1.25rem;
}

:deep(.traceroute-map-port-cluster__list) {
    max-height: 9rem;
    margin: 0.45rem 0 0;
    overflow-y: auto;
    padding-left: 1rem;
}
</style>
