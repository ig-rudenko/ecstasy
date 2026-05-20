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
                v-tooltip.bottom="maximized ? 'Выйти из полного экрана' : 'На весь экран'"
                @click="toggleMaximize"
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
            На карте показано {{ data.nodes.length }} узлов, включая {{ inheritedNodesCount }} узлов с координатами,
            унаследованными от соседнего оборудования. Пропущено {{ data.skipped_nodes.length }} узлов без координат и
            без подходящего соседнего устройства.
        </div>
    </section>
</template>

<script setup lang="ts">
import "leaflet/dist/leaflet.css";

import {
    circleMarker,
    Control,
    featureGroup,
    latLngBounds,
    Map as LMap,
    polyline,
    tileLayer,
    type CircleMarker,
    type FeatureGroup,
    type LatLngExpression,
    type Polyline,
    type TileLayer,
} from "leaflet";
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
let map: LMap | null = null;
let nodesLayer: FeatureGroup<CircleMarker> | null = null;
let portsLayer: FeatureGroup<CircleMarker> | null = null;
let edgesLayer: FeatureGroup<Polyline> | null = null;
let layersControl: Control.Layers | null = null;
let resizeObserver: ResizeObserver | null = null;
let refreshAnimationFrame: number | null = null;
let selectedEdgeLine: Polyline | null = null;
const markersById = new Map<string, CircleMarker>();
const edgeDefaultStyles = new WeakMap<Polyline, EdgeStyle>();
const foundNodeIds = ref(new Set<string>());
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
const inheritedNodesCount = computed(() => props.data.nodes.filter((node) => node.inherited_from).length);

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
    map.createPane("tracerouteNodes");
    map.createPane("traceroutePorts");
    map.getPane("tracerouteEdges")!.style.zIndex = "410";
    map.getPane("tracerouteNodes")!.style.zIndex = "430";
    map.getPane("traceroutePorts")!.style.zIndex = "440";
    map.setView([44.6, 33.5], 12);
    map.attributionControl.getContainer()?.remove();
    map.addControl(new Control.Scale());
    edgesLayer = featureGroup<Polyline>().addTo(map);
    nodesLayer = featureGroup<CircleMarker>().addTo(map);
    portsLayer = featureGroup<CircleMarker>().addTo(map);
    layersControl = new Control.Layers(
        {
            OSM: tiles.osm,
            Google: tiles.geoGoogle,
            ArcGIS: tiles.arcgisonline,
        },
        {
            Узлы: nodesLayer,
            Порты: portsLayer,
            Связи: edgesLayer,
        }
    ).addTo(map);
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
function renderMap(): void {
    initMap();
    if (!map || !nodesLayer || !portsLayer || !edgesLayer) {
        return;
    }

    nodesLayer.clearLayers();
    portsLayer.clearLayers();
    edgesLayer.clearLayers();
    markersById.clear();
    selectedEdgeLine = null;

    const nodesById = new Map<string, TracerouteMapNode>();
    for (const node of props.data.nodes) {
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
            pane: "tracerouteEdges",
            ...edgeStyle,
        });
        edgeDefaultStyles.set(line, edgeStyle);
        line.bindTooltip(createEdgeTooltip(edge, source, target), { sticky: true });
        line.bindPopup(createEdgePopup(edge, null, false));
        line.on("click", () => {
            selectEdgeLine(line, edge);
            loadEdgeInterfaceInfo(edge, line);
        });
        line.addTo(edgesLayer);
    }

    for (const node of props.data.nodes) {
        const markerStyle = node.inherited_from
            ? {
                  radius: 5,
                  color: "#fde68a",
                  weight: 2,
                  fillColor: "#f59e0b",
                  fillOpacity: 0.95,
              }
            : defaultMarkerStyle;
        const marker = circleMarker([node.lat, node.lon], {
            ...markerStyle,
            pane: node.inherited_from ? "traceroutePorts" : "tracerouteNodes",
        });
        marker.bindTooltip(node.label, { direction: "top", sticky: true });
        marker.bindPopup(createNodePopup(node));
        marker.addTo(node.inherited_from ? portsLayer : nodesLayer);
        marker.bringToFront();
        markersById.set(node.id, marker);
    }
    applySearchHighlight();

    const points = props.data.nodes.map((node) => [node.lat, node.lon] as LatLngExpression);
    if (points.length) {
        map.fitBounds(latLngBounds(points), { padding: [40, 40], maxZoom: 17 });
    }
    refreshMapLayout();
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
                : node?.inherited_from
                  ? {
                        radius: 5,
                        color: "#fde68a",
                        weight: 2,
                        fillColor: "#f59e0b",
                        fillOpacity: 0.95,
                    }
                  : defaultMarkerStyle
        );
        marker.bringToFront();
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
function rebuildMap(): void {
    destroyMap();
    nextTick(() => {
        renderMap();
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
    if (selectedEdgeLine && selectedEdgeLine !== line) {
        selectedEdgeLine.setStyle(edgeDefaultStyles.get(selectedEdgeLine) || getDefaultEdgeStyle(edge));
    }
    selectedEdgeLine = line;
    line.setStyle({
        color: "#f97316",
        opacity: 0.95,
        weight: Math.max(3, Math.min(Number(edge.value || 2) + 1, 5)),
    });
    line.bringToFront();
}

interface EdgeStyle {
    color: string;
    opacity: number;
    weight: number;
}

/**
 * Returns default edge style.
 */
function getDefaultEdgeStyle(edge: TracerouteMapEdge): EdgeStyle {
    return {
        color: "#38bdf8",
        opacity: 0.65,
        weight: Math.max(1, Math.min(Number(edge.value || 1), 3)),
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
    () => nextTick(renderMap),
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
    portsLayer = null;
    edgesLayer = null;
    layersControl = null;
    markersById.clear();
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
</style>
