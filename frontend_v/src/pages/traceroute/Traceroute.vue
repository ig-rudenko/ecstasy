<template>
    <div class="mx-auto max-w-7xl py-2 sm:px-6 sm:py-6 lg:px-8">
        <div class="flex flex-col gap-4 sm:gap-6">
            <TracerouteHero :model-value="tracerouteMode" @update:model-value="setTracerouteMode" />

            <TracerouteVisualizationSwitch
                :model-value="visualizationMode"
                @update:model-value="setVisualizationMode"
            />

            <TracerouteVlanForm
                :mode="tracerouteMode"
                :input="input"
                :input-vlan-info="inputVlanInfo"
                :options="vlanTracerouteOptions"
                :started="tracerouteStarted"
                @load="loadCurrentTraceroute"
                @vlan-info="getInputVlanInfo"
                @update:vlan="setVlan"
                @update:option="updateVlanTracerouteOption"
            />

            <TracerouteMacForm
                :mode="tracerouteMode"
                :input="input"
                :options="vlanTracerouteOptions"
                :mac-options="macTracerouteOptions"
                :started="tracerouteStarted"
                @load="loadCurrentTraceroute"
                @update:mac="setMac"
                @update:mac-vlan-filter="setMacVlanFilter"
                @update:option="updateVlanTracerouteOption"
            />

            <div v-if="tracerouteStarted" class="flex justify-center py-10">
                <div
                    class="inline-flex flex-col items-center gap-4 rounded-3xl border border-gray-200/70 bg-white/80 px-10 py-8 backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/50"
                >
                    <ProgressSpinner class="w-16! h-16!" stroke-width="3" />
                    <span class="text-sm text-gray-600 dark:text-gray-300">
                        {{ visualizationMode === "map" ? "Строим карту..." : "Строим граф..." }}
                    </span>
                </div>
            </div>

            <div v-else-if="tracerouteNotFound" class="flex justify-center py-10">
                <div
                    class="w-full max-w-xl rounded-3xl border border-dashed border-gray-300 bg-white/80 px-6 py-8 text-center shadow-sm dark:border-gray-700 dark:bg-gray-900/50"
                >
                    <div class="text-base font-semibold text-gray-900 dark:text-gray-100">Трассировка не найдена</div>
                    <div class="mt-2 text-sm text-gray-600 dark:text-gray-300">
                        По указанным параметрам не вернулись узлы и связи для отображения.
                    </div>
                </div>
            </div>

            <TracerouteVlanBadges
                v-if="tracerouteMode === 'mac'"
                :items="macTracerouteVLANInfo"
                :active-vlan="macTracerouteOptions.vlanFilter"
                @select="tracerouteMACWithVlanFilter"
            />

            <TracerouteGraphArea
                v-if="graphVisible"
                :mode="tracerouteMode"
                :vlan-rendered="vlanTracerouteOptions.rendered"
                :mac-rendered="macTracerouteOptions.rendered"
                :maximized="visualizationMaximized"
                :graph-node-search="graphNodeSearch"
                :graph-search-matches-count="graphSearchMatchesCount"
                :graph-search-match-index="graphSearchMatchIndex"
                :graph-render-loading="graphRenderLoading"
                :graph-render-progress="graphRenderProgress"
                :physics-menu-visible="physicsMenuVisible"
                @update:graph-node-search="graphNodeSearch = $event"
                @focus-node="focusGraphNode"
                @toggle-physics="togglePhysicsMenu"
                @toggle-maximize="toggleVisualizationMaximized"
            />

            <TracerouteMapArea
                v-if="mapVisible && tracerouteMapData"
                :data="tracerouteMapData"
                :maximized="visualizationMaximized"
                @toggle-maximize="toggleVisualizationMaximized"
            />
        </div>
    </div>

    <TracerouteNodeDialog
        v-model:visible="nodeInfoPopupVisible"
        :node="selectedTracerouteNode"
        :node-id="selectedTracerouteNodeId"
        :node-label="selectedTracerouteNodeLabel"
        :title-html="selectedTracerouteNodeTitleHtml"
        :device-route-available="!!selectedTracerouteDeviceRoute"
        :device-href="selectedTracerouteDeviceHref"
        @hide="closeTracerouteNodePopup"
    />
</template>

<script lang="ts">
import { defineComponent, markRaw } from "vue";

import api from "@/services/api";
import router from "@/router";
import { getInputVlanInfo } from "@/services/traceroute";
import { InputNumberInputEvent } from "primevue";
import TracerouteNetwork, { type TracerouteNodeData } from "./net";
import TracerouteGraphArea from "./components/TracerouteGraphArea.vue";
import TracerouteHero from "./components/TracerouteHero.vue";
import TracerouteMapArea from "./components/TracerouteMapArea.vue";
import TracerouteMacForm from "./components/TracerouteMacForm.vue";
import TracerouteNodeDialog from "./components/TracerouteNodeDialog.vue";
import TracerouteVlanBadges from "./components/TracerouteVlanBadges.vue";
import TracerouteVlanForm from "./components/TracerouteVlanForm.vue";
import TracerouteVisualizationSwitch from "./components/TracerouteVisualizationSwitch.vue";
import type {
    TracerouteMapData,
    TracerouteMode,
    TracerouteVisualizationMode,
    TrunkFilterMode,
    VlanCountInfo,
    VlanTracerouteOptions,
} from "./components/types";

export default defineComponent({
    name: "Traceroute",
    components: {
        TracerouteGraphArea,
        TracerouteHero,
        TracerouteMapArea,
        TracerouteMacForm,
        TracerouteNodeDialog,
        TracerouteVisualizationSwitch,
        TracerouteVlanBadges,
        TracerouteVlanForm,
    },
    data() {
        return {
            vlanTracerouteStarted: false,
            macTracerouteStarted: false,
            mapTracerouteStarted: false,
            tracerouteMode: "vlan" as TracerouteMode,
            visualizationMode: "map" as TracerouteVisualizationMode,
            input: {
                vlan: null as number | null,
                mac: "",
            },
            inputVlanInfo: {
                name: "",
                description: "",
            },
            vlanTracerouteOptions: {
                adminDownPorts: false,
                showEmptyPorts: false,
                doubleCheckVlan: true,
                graphMinLength: 3,
                trunkFilterMode: "mark_broad",
                deviceNameFilter: "",
                groupFilter: "",
                nodesOnly: false,
                rendered: false,
            } as VlanTracerouteOptions,
            macTracerouteOptions: {
                rendered: false,
                vlanFilter: null as number | null,
            },
            visualizationMaximized: false,
            macTracerouteVLANInfo: [] as VlanCountInfo[],
            tracerouteMapData: null as TracerouteMapData | null,
            mapRendered: false,
            tracerouteNotFound: false,
            vlanNetwork: markRaw(new TracerouteNetwork("vlan-network")),
            macNetwork: markRaw(new TracerouteNetwork("mac-network")),
            graphNodeSearch: "",
            graphSearchMatchesCount: 0,
            graphSearchMatchIndex: 0,
            graphRenderLoading: false,
            graphRenderProgress: 0,
            physicsMenuVisible: false,
            vlanAbortController: null as AbortController | null,
            macAbortController: null as AbortController | null,
            mapAbortController: null as AbortController | null,
            activeRenderRequestId: 0,
            nodeInfoPopupVisible: false,
            selectedTracerouteNode: null as TracerouteNodeData | null,
        };
    },
    computed: {
        graphVisible(): boolean {
            if (this.visualizationMode !== "graph") {
                return false;
            }
            if (this.graphRenderLoading) {
                return true;
            }
            return this.tracerouteMode === "mac"
                ? this.macTracerouteOptions.rendered
                : this.vlanTracerouteOptions.rendered;
        },
        mapVisible(): boolean {
            return this.visualizationMode === "map" && this.mapRendered;
        },
        tracerouteStarted(): boolean {
            return this.vlanTracerouteStarted || this.macTracerouteStarted || this.mapTracerouteStarted;
        },
        selectedTracerouteNodeId(): string {
            if (!this.selectedTracerouteNode) {
                return "";
            }
            return String(this.selectedTracerouteNode.id ?? "");
        },
        selectedTracerouteNodeLabel(): string {
            if (!this.selectedTracerouteNode) {
                return "";
            }
            return String(this.selectedTracerouteNode.label ?? this.selectedTracerouteNode.id ?? "");
        },
        selectedTracerouteNodeTitleHtml(): string {
            if (!this.selectedTracerouteNode || typeof this.selectedTracerouteNode.title !== "string") {
                return "";
            }
            return this.selectedTracerouteNode.title;
        },
        selectedTracerouteDeviceName(): string | null {
            if (!this.selectedTracerouteNode) {
                return null;
            }

            const rawId =
                typeof this.selectedTracerouteNode.id === "string" ? this.selectedTracerouteNode.id.trim() : "";
            const rawLabel =
                typeof this.selectedTracerouteNode.label === "string"
                    ? this.selectedTracerouteNode.label.trim()
                    : String(this.selectedTracerouteNode.label ?? "").trim();

            if (!rawId || /^\d+$/.test(rawId)) {
                return null;
            }
            if (rawId.includes("-->")) {
                return null;
            }

            const loweredId = rawId.toLowerCase();
            if (loweredId.includes("p:(") || loweredId.includes("d:(")) {
                return null;
            }
            if (rawLabel && rawLabel !== rawId) {
                return null;
            }

            return rawId;
        },
        selectedTracerouteDeviceRoute(): null | { name: string; params: { deviceName: string } } {
            if (!this.selectedTracerouteDeviceName) {
                return null;
            }
            return {
                name: "device",
                params: {
                    deviceName: this.selectedTracerouteDeviceName,
                },
            };
        },
        selectedTracerouteDeviceHref(): string {
            if (!this.selectedTracerouteDeviceRoute) {
                return "";
            }
            return router.resolve(this.selectedTracerouteDeviceRoute).href;
        },
    },
    mounted() {
        this.vlanNetwork.setNodeClickHandler((node) => this.handleTracerouteNodeClick(node));
        this.macNetwork.setNodeClickHandler((node) => this.handleTracerouteNodeClick(node));
        this.vlanNetwork.setRenderProgressHandler((progress) => this.handleGraphRenderProgress(progress));
        this.macNetwork.setRenderProgressHandler((progress) => this.handleGraphRenderProgress(progress));

        if (this.applyTracerouteParamsFromUrl() && this.hasRequiredTracerouteInput()) {
            this.loadCurrentTraceroute();
        }
    },
    unmounted() {
        this.cancelOngoingTraceroute();
        this.vlanNetwork.cancelRender();
        this.macNetwork.cancelRender();
    },
    methods: {
        getQueryStringValue(name: string): string {
            const value = this.$route.query[name];

            if (Array.isArray(value)) {
                return typeof value[0] === "string" ? value[0] : "";
            }

            return typeof value === "string" ? value : "";
        },
        getQueryNumberValue(name: string): number | null {
            const value = Number(this.getQueryStringValue(name));

            return Number.isFinite(value) && value > 0 ? value : null;
        },
        getQueryBooleanValue(name: string, fallback: boolean): boolean {
            const value = this.getQueryStringValue(name);

            if (value === "true") {
                return true;
            }
            if (value === "false") {
                return false;
            }

            return fallback;
        },
        isTracerouteMode(value: string): value is TracerouteMode {
            return value === "vlan" || value === "mac" || value === "neighbors";
        },
        isVisualizationMode(value: string): value is TracerouteVisualizationMode {
            return value === "graph" || value === "map";
        },
        isTrunkFilterMode(value: string): value is TrunkFilterMode {
            return value === "off" || value === "mark_broad" || value === "hide_broad";
        },
        hasTracerouteUrlParams(): boolean {
            const queryKeys = [
                "mode",
                "tracerouteMode",
                "visualization_mode",
                "visualizationMode",
                "maximized",
                "vlan",
                "mac",
                "ep",
                "ad",
                "double_check",
                "graph_min_length",
                "nodes_only",
                "trunk_filter_mode",
                "mac_vlan",
                "device_name",
                "group",
            ];

            return queryKeys.some((key) => this.$route.query[key] !== undefined);
        },
        applyTracerouteParamsFromUrl(): boolean {
            if (!this.hasTracerouteUrlParams()) {
                return false;
            }

            const mode = this.getQueryStringValue("mode") || this.getQueryStringValue("tracerouteMode");
            if (this.isTracerouteMode(mode)) {
                this.tracerouteMode = mode;
            }

            const visualizationMode =
                this.getQueryStringValue("visualization_mode") || this.getQueryStringValue("visualizationMode");
            if (this.isVisualizationMode(visualizationMode)) {
                this.visualizationMode = visualizationMode;
            }
            this.visualizationMaximized = this.getQueryBooleanValue("maximized", this.visualizationMaximized);

            const vlan = this.getQueryNumberValue("vlan");
            if (vlan !== null) {
                this.input.vlan = vlan;
                getInputVlanInfo(vlan).then((value) => (this.inputVlanInfo = value));
            }

            const mac = this.getQueryStringValue("mac");
            if (mac) {
                this.input.mac = mac;
            }

            const macVlan = this.getQueryNumberValue("mac_vlan");
            this.macTracerouteOptions.vlanFilter = macVlan;

            this.vlanTracerouteOptions.showEmptyPorts = this.getQueryBooleanValue(
                "ep",
                this.vlanTracerouteOptions.showEmptyPorts
            );
            this.vlanTracerouteOptions.adminDownPorts = this.getQueryBooleanValue(
                "ad",
                this.vlanTracerouteOptions.adminDownPorts
            );
            this.vlanTracerouteOptions.doubleCheckVlan = this.getQueryBooleanValue(
                "double_check",
                this.vlanTracerouteOptions.doubleCheckVlan
            );
            this.vlanTracerouteOptions.nodesOnly = this.getQueryBooleanValue(
                "nodes_only",
                this.vlanTracerouteOptions.nodesOnly
            );

            const graphMinLength = this.getQueryNumberValue("graph_min_length");
            if (graphMinLength !== null) {
                this.vlanTracerouteOptions.graphMinLength = graphMinLength;
            }

            const trunkFilterMode = this.getQueryStringValue("trunk_filter_mode");
            if (this.isTrunkFilterMode(trunkFilterMode)) {
                this.vlanTracerouteOptions.trunkFilterMode = trunkFilterMode;
            }

            this.vlanTracerouteOptions.deviceNameFilter = this.getQueryStringValue("device_name");
            this.vlanTracerouteOptions.groupFilter = this.getQueryStringValue("group");

            return true;
        },
        createTracerouteUrlParams(): URLSearchParams {
            const params = this.createTracerouteParams();
            params.set("visualization_mode", this.visualizationMode);
            params.set("maximized", String(this.visualizationMaximized));
            return params;
        },
        syncTracerouteUrlParams() {
            const params = this.createTracerouteUrlParams();

            if (params.toString() === this.getCurrentTracerouteQueryString()) {
                return;
            }

            void router
                .replace({
                    name: "tools-traceroute",
                    query: Object.fromEntries(params.entries()),
                })
                .catch(() => undefined);
        },
        getCurrentTracerouteQueryString(): string {
            const params = new URLSearchParams();

            Object.entries(this.$route.query).forEach(([key, value]) => {
                if (Array.isArray(value)) {
                    value.forEach((item) => {
                        if (typeof item === "string") {
                            params.append(key, item);
                        }
                    });
                    return;
                }

                if (typeof value === "string") {
                    params.set(key, value);
                }
            });

            return params.toString();
        },
        setVlan(value: number | null) {
            this.input.vlan = value;
            this.syncTracerouteUrlParams();
        },
        setMac(value: string) {
            this.input.mac = value;
            this.syncTracerouteUrlParams();
        },
        setMacVlanFilter(value: number | null) {
            this.macTracerouteOptions.vlanFilter = value;
            this.syncTracerouteUrlParams();
        },
        setTracerouteMode(mode: TracerouteMode) {
            if (this.tracerouteMode !== mode) {
                this.visualizationMaximized = false;
                this.mapRendered = false;
                this.tracerouteMapData = null;
                this.tracerouteNotFound = false;
                this.closeTracerouteNodePopup();
            }
            this.tracerouteMode = mode;
            this.syncTracerouteUrlParams();
        },
        setVisualizationMode(mode: TracerouteVisualizationMode) {
            if (this.visualizationMode === mode) {
                return;
            }
            if (this.visualizationMode === "graph") {
                this.cancelGraphRender();
            } else {
                this.cancelMapRender();
            }
            this.visualizationMode = mode;
            this.syncTracerouteUrlParams();
            if (!this.hasRequiredTracerouteInput()) {
                return;
            }
            if (mode === "map" && !this.mapRendered) {
                this.load_traceroute_map();
                return;
            }
            if (
                mode === "graph" &&
                (this.tracerouteMode === "mac"
                    ? !this.macTracerouteOptions.rendered
                    : !this.vlanTracerouteOptions.rendered)
            ) {
                this.loadCurrentTraceroute();
            }
        },
        updateVlanTracerouteOption(key: keyof VlanTracerouteOptions, value: string | number | boolean | null) {
            (this.vlanTracerouteOptions[key] as string | number | boolean | null) = value;
            this.syncTracerouteUrlParams();
        },
        getInputVlanInfo(event: InputNumberInputEvent) {
            const vid = parseInt(event.value?.toString() || "");
            getInputVlanInfo(vid).then((value) => (this.inputVlanInfo = value));
        },
        /**
         * Открывает popup с информацией о выбранном узле графа.
         */
        handleTracerouteNodeClick(node: TracerouteNodeData | null) {
            if (!node) {
                this.closeTracerouteNodePopup();
                return;
            }
            this.selectedTracerouteNode = node;
            this.nodeInfoPopupVisible = true;
        },
        /**
         * Сбрасывает выбранный узел и скрывает popup.
         */
        closeTracerouteNodePopup() {
            this.nodeInfoPopupVisible = false;
            this.selectedTracerouteNode = null;
        },
        handleGraphRenderProgress(progress: number) {
            this.graphRenderProgress = Math.max(0, Math.min(100, progress));
            this.graphRenderLoading = this.graphRenderProgress < 100;
        },
        startGraphRenderProgress() {
            this.graphRenderProgress = 0;
            this.graphRenderLoading = true;
        },
        finishGraphRenderProgress() {
            this.graphRenderProgress = 100;
            window.setTimeout(() => {
                if (this.graphRenderProgress === 100) {
                    this.graphRenderLoading = false;
                }
            }, 350);
        },
        cancelOngoingTraceroute() {
            this.cancelGraphRender();
            this.cancelMapRender();
        },
        cancelGraphRender() {
            this.activeRenderRequestId += 1;
            this.vlanAbortController?.abort();
            this.vlanAbortController = null;
            this.macAbortController?.abort();
            this.macAbortController = null;
            this.vlanNetwork.cancelRender();
            this.macNetwork.cancelRender();
            this.vlanTracerouteStarted = false;
            this.macTracerouteStarted = false;
            this.graphRenderLoading = false;
            this.graphRenderProgress = 0;
            this.vlanTracerouteOptions.rendered = false;
            this.macTracerouteOptions.rendered = false;
            this.graphSearchMatchesCount = 0;
            this.graphSearchMatchIndex = 0;
            this.closeTracerouteNodePopup();
        },
        cancelMapRender() {
            this.activeRenderRequestId += 1;
            this.mapAbortController?.abort();
            this.mapAbortController = null;
            this.mapTracerouteStarted = false;
            this.mapRendered = false;
            this.tracerouteMapData = null;
        },
        resetTracerouteNotFound() {
            this.tracerouteNotFound = false;
        },
        markTracerouteNotFound() {
            this.vlanTracerouteStarted = false;
            this.macTracerouteStarted = false;
            this.mapTracerouteStarted = false;
            this.graphRenderLoading = false;
            this.graphRenderProgress = 0;
            this.vlanTracerouteOptions.rendered = false;
            this.macTracerouteOptions.rendered = false;
            this.mapRendered = false;
            this.tracerouteMapData = null;
            this.tracerouteNotFound = true;
        },
        hasRenderableTracerouteData(data: unknown): boolean {
            const payload = data as { nodes?: unknown; edges?: unknown } | null;
            return (
                Array.isArray(payload?.nodes) &&
                payload.nodes.length > 0 &&
                Array.isArray(payload?.edges) &&
                payload.edges.length > 0
            );
        },
        focusGraphNode() {
            const network = this.tracerouteMode === "mac" ? this.macNetwork : this.vlanNetwork;
            const result = network.focusNodeByName(this.graphNodeSearch);
            this.graphSearchMatchesCount = result.count;
            this.graphSearchMatchIndex = result.current;
        },
        togglePhysicsMenu() {
            this.physicsMenuVisible = !this.physicsMenuVisible;
            this.vlanNetwork.setPhysicsConfiguratorVisible(this.physicsMenuVisible);
            this.macNetwork.setPhysicsConfiguratorVisible(this.physicsMenuVisible);
        },
        toggleVisualizationMaximized() {
            this.visualizationMaximized = !this.visualizationMaximized;
            this.syncTracerouteUrlParams();
            if (this.visualizationMaximized && this.visualizationMode === "graph") {
                const networkElementId = this.tracerouteMode === "mac" ? "mac-network" : "vlan-network";
                setTimeout(() =>
                    document.getElementById(networkElementId)?.scrollIntoView({ behavior: "instant", block: "end" })
                );
            }
        },
        hasRequiredTracerouteInput(): boolean {
            if (this.tracerouteMode === "vlan") {
                return !!this.input.vlan;
            }
            if (this.tracerouteMode === "mac") {
                return !!this.validateMac(this.input.mac).length;
            }
            return true;
        },
        loadCurrentTraceroute() {
            this.syncTracerouteUrlParams();

            if (this.visualizationMode === "map") {
                this.load_traceroute_map();
                return;
            }
            if (this.tracerouteMode === "mac") {
                this.load_mac_traceroute();
                return;
            }
            this.load_traceroute();
        },
        createTracerouteParams(): URLSearchParams {
            const params = new URLSearchParams({
                mode: this.tracerouteMode,
                ep: String(this.vlanTracerouteOptions.showEmptyPorts),
                ad: String(this.vlanTracerouteOptions.adminDownPorts),
                double_check: String(this.vlanTracerouteOptions.doubleCheckVlan),
                graph_min_length: String(this.vlanTracerouteOptions.graphMinLength),
                nodes_only: String(this.vlanTracerouteOptions.nodesOnly),
            });
            if (this.tracerouteMode === "vlan" && this.input.vlan) {
                params.append("vlan", String(this.input.vlan));
                params.append("trunk_filter_mode", this.vlanTracerouteOptions.trunkFilterMode);
            }
            if (this.tracerouteMode === "mac") {
                params.append("mac", this.validateMac(this.input.mac));
                if (this.macTracerouteOptions.vlanFilter) {
                    params.append("mac_vlan", String(this.macTracerouteOptions.vlanFilter));
                }
            }
            const deviceNameFilter = this.vlanTracerouteOptions.deviceNameFilter.trim();
            if (deviceNameFilter) {
                params.append("device_name", deviceNameFilter);
            }
            const groupFilter = this.vlanTracerouteOptions.groupFilter.trim();
            if (groupFilter) {
                params.append("group", groupFilter);
            }
            return params;
        },
        /**
         * Отправляем на сервер запрос трассировки указанного в поле для ввода VLAN.
         * И создаем в определенном блоке граф для данной трассировки.
         */
        load_traceroute() {
            if (this.tracerouteMode === "vlan" && !this.input.vlan) return;

            this.cancelMapRender();
            this.cancelGraphRender();
            this.resetTracerouteNotFound();
            this.closeTracerouteNodePopup();
            const requestId = ++this.activeRenderRequestId;
            this.vlanTracerouteStarted = true;
            this.startGraphRenderProgress();
            const controller = new AbortController();
            this.vlanAbortController = controller;

            const params = this.createTracerouteParams();

            api.get("/api/v1/tools/traceroute?" + params.toString(), { signal: controller.signal })
                .then(async (resp) => {
                    if (requestId !== this.activeRenderRequestId) {
                        return;
                    }
                    if (!this.hasRenderableTracerouteData(resp.data)) {
                        this.markTracerouteNotFound();
                        return;
                    }
                    const rendered = await this.vlanNetwork.renderVisualData(
                        resp.data.nodes,
                        resp.data.edges,
                        resp.data.options
                    );
                    if (!rendered || requestId !== this.activeRenderRequestId) {
                        return;
                    }
                    this.vlanTracerouteStarted = false;
                    this.vlanTracerouteOptions.rendered = true;
                    this.finishGraphRenderProgress();
                })
                .catch((error) => {
                    if (requestId !== this.activeRenderRequestId || error?.code === "ERR_CANCELED") {
                        return;
                    }
                    this.vlanTracerouteStarted = false;
                    this.finishGraphRenderProgress();
                })
                .finally(() => {
                    if (this.vlanAbortController === controller) {
                        this.vlanAbortController = null;
                    }
                });
        },
        // Удаляет из MAC адреса все символы, не являющиеся шестнадцатеричными.
        validateMac(mac: string): string {
            return String(mac).replace(/\W/g, "");
        },
        /**
         * Отправляем на сервер запрос трассировки указанного в поле для ввода MAC.
         * И создаем в определенном блоке граф для данной трассировки.
         */
        load_mac_traceroute() {
            const validMac = this.validateMac(this.input.mac);
            if (!validMac.length) return;

            this.cancelMapRender();
            this.cancelGraphRender();
            this.resetTracerouteNotFound();
            this.closeTracerouteNodePopup();
            const requestId = ++this.activeRenderRequestId;
            this.macTracerouteStarted = true;
            this.startGraphRenderProgress();
            const controller = new AbortController();
            this.macAbortController = controller;
            const params = this.createTracerouteParams();

            api.get("/api/v1/tools/traceroute?" + params.toString(), { signal: controller.signal })
                .then(async (resp) => {
                    if (requestId !== this.activeRenderRequestId) {
                        return;
                    }
                    if (!this.hasRenderableTracerouteData(resp.data)) {
                        this.markTracerouteNotFound();
                        return;
                    }
                    const rendered = await this.macNetwork.renderVisualData(
                        resp.data.nodes,
                        resp.data.edges,
                        resp.data.options
                    );
                    if (!rendered || requestId !== this.activeRenderRequestId) {
                        return;
                    }
                    this.macTracerouteVLANInfo = resp.data.vlansInfo;
                    this.macTracerouteStarted = false;
                    this.macTracerouteOptions.rendered = true;
                    this.finishGraphRenderProgress();
                })
                .catch((error) => {
                    if (requestId !== this.activeRenderRequestId || error?.code === "ERR_CANCELED") {
                        return;
                    }
                    this.macTracerouteStarted = false;
                    this.finishGraphRenderProgress();
                })
                .finally(() => {
                    if (this.macAbortController === controller) {
                        this.macAbortController = null;
                    }
                });
        },
        load_traceroute_map() {
            if (!this.hasRequiredTracerouteInput()) return;

            this.cancelGraphRender();
            this.cancelMapRender();
            this.resetTracerouteNotFound();
            this.closeTracerouteNodePopup();
            const requestId = ++this.activeRenderRequestId;
            this.mapTracerouteStarted = true;
            this.mapRendered = false;
            this.tracerouteMapData = null;
            const controller = new AbortController();
            this.mapAbortController = controller;

            api.get("/api/v1/tools/traceroute-map?" + this.createTracerouteParams().toString(), {
                signal: controller.signal,
            })
                .then((resp) => {
                    if (requestId !== this.activeRenderRequestId) {
                        return;
                    }
                    if (!this.hasRenderableTracerouteData(resp.data)) {
                        this.markTracerouteNotFound();
                        return;
                    }
                    this.tracerouteMapData = resp.data;
                    this.mapRendered = true;
                    if (this.tracerouteMode === "mac" && resp.data.vlansInfo) {
                        this.macTracerouteVLANInfo = resp.data.vlansInfo;
                    }
                })
                .catch((error) => {
                    if (requestId !== this.activeRenderRequestId || error?.code === "ERR_CANCELED") {
                        return;
                    }
                })
                .finally(() => {
                    if (this.mapAbortController === controller) {
                        this.mapAbortController = null;
                    }
                    if (requestId === this.activeRenderRequestId) {
                        this.mapTracerouteStarted = false;
                    }
                });
        },
        tracerouteMACWithVlanFilter(vlan: number) {
            this.macTracerouteOptions.vlanFilter = this.macTracerouteOptions.vlanFilter === vlan ? null : vlan;
            this.syncTracerouteUrlParams();
            this.loadCurrentTraceroute();
        },
    },
});
</script>

<style>
html body .vis-configuration-wrapper,
html body .vis-configuration.vis-configuration-wrapper {
    position: absolute !important;
    font-family: monospace !important;
    top: 3.5rem !important;
    right: 0.5rem !important;
    left: auto !important;
    bottom: auto !important;
    z-index: 10003 !important;
    max-height: calc(100% - 4.25rem) !important;
    width: min(34rem, calc(100% - 1rem)) !important;
    overflow: auto !important;
    border: 1px solid rgba(71, 85, 105, 0.7) !important;
    border-radius: 0.9rem !important;
    background: rgba(2, 6, 23, 0.9) !important;
    color: #e2e8f0 !important;
    backdrop-filter: blur(3px);
    padding: 0.55rem 0.65rem !important;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45) !important;
}

html body .vis-configuration,
html body .vis-configuration .vis-configuration-item,
html body .vis-configuration label,
html body .vis-configuration select,
html body .vis-configuration input,
html body .vis-configuration .vis-configuration-popup {
    color: #e2e8f0 !important;
    background-color: transparent !important;
    border-color: rgba(100, 116, 139, 0.65) !important;
}

html body .vis-configuration option {
    color: #e2e8f0 !important;
    background-color: #000000 !important;
    border-color: rgba(100, 116, 139, 0.65) !important;
}

html body .vis-configuration select,
html body .vis-configuration input {
    border-radius: 0.45rem !important;
}
</style>
