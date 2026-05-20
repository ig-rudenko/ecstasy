<template>
    <Header />

    <div class="mx-auto max-w-7xl px-4 py-2 sm:px-6 sm:py-6 lg:px-8">
        <div class="flex flex-col gap-4 sm:gap-6">
            <TracerouteHero :model-value="tracerouteMode" @update:model-value="setTracerouteMode" />

            <TracerouteVlanForm
                :mode="tracerouteMode"
                :input="input"
                :input-vlan-info="inputVlanInfo"
                :options="vlanTracerouteOptions"
                :started="vlanTracerouteStarted"
                @load="load_traceroute"
                @vlan-info="getInputVlanInfo"
                @update:vlan="input.vlan = $event"
                @update:option="updateVlanTracerouteOption"
            />

            <TracerouteMacForm
                :mode="tracerouteMode"
                :input="input"
                :options="vlanTracerouteOptions"
                :mac-options="macTracerouteOptions"
                :started="macTracerouteStarted"
                @load="load_mac_traceroute"
                @update:mac="input.mac = $event"
                @update:mac-vlan-filter="macTracerouteOptions.vlanFilter = $event"
                @update:option="updateVlanTracerouteOption"
            />

            <div v-if="vlanTracerouteStarted || macTracerouteStarted" class="flex justify-center py-10">
                <div
                    class="inline-flex flex-col items-center gap-4 rounded-3xl border border-gray-200/70 bg-white/80 px-10 py-8 backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/50"
                >
                    <ProgressSpinner class="w-16! h-16!" stroke-width="3" />
                    <span class="text-sm text-gray-600 dark:text-gray-300">Строим граф...</span>
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
                :vlan-maximized="vlanTracerouteOptions.maximized"
                :mac-maximized="macTracerouteOptions.maximized"
                :maximized="graphMaximized"
                :graph-node-search="graphNodeSearch"
                :graph-search-matches-count="graphSearchMatchesCount"
                :graph-search-match-index="graphSearchMatchIndex"
                :graph-render-loading="graphRenderLoading"
                :graph-render-progress="graphRenderProgress"
                :physics-menu-visible="physicsMenuVisible"
                @update:graph-node-search="graphNodeSearch = $event"
                @focus-node="focusGraphNode"
                @toggle-physics="togglePhysicsMenu"
                @toggle-maximize-vlan="toggleMaximizeVlanTraceroute"
                @toggle-maximize-mac="toggleMaximizeMACTraceroute"
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

    <Footer />
</template>

<script lang="ts">
import { defineComponent, markRaw } from "vue";

import api from "@/services/api";
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";
import router from "@/router";
import { getInputVlanInfo } from "@/services/traceroute";
import { InputNumberInputEvent } from "primevue";
import TracerouteNetwork, { type TracerouteNodeData } from "./net";
import TracerouteGraphArea from "./components/TracerouteGraphArea.vue";
import TracerouteHero from "./components/TracerouteHero.vue";
import TracerouteMacForm from "./components/TracerouteMacForm.vue";
import TracerouteNodeDialog from "./components/TracerouteNodeDialog.vue";
import TracerouteVlanBadges from "./components/TracerouteVlanBadges.vue";
import TracerouteVlanForm from "./components/TracerouteVlanForm.vue";
import type { TracerouteMode, VlanCountInfo, VlanTracerouteOptions } from "./components/types";

export default defineComponent({
    name: "Traceroute",
    components: {
        Footer,
        Header,
        TracerouteGraphArea,
        TracerouteHero,
        TracerouteMacForm,
        TracerouteNodeDialog,
        TracerouteVlanBadges,
        TracerouteVlanForm,
    },
    data() {
        return {
            vlanTracerouteStarted: false,
            macTracerouteStarted: false,
            tracerouteMode: "vlan" as TracerouteMode,
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
                deviceNameFilter: "",
                groupFilter: "",
                nodesOnly: false,
                maximized: false,
                rendered: false,
            } as VlanTracerouteOptions,
            macTracerouteOptions: {
                maximized: false,
                rendered: false,
                vlanFilter: null as number | null,
            },
            macTracerouteVLANInfo: [] as VlanCountInfo[],
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
            activeRenderRequestId: 0,
            nodeInfoPopupVisible: false,
            selectedTracerouteNode: null as TracerouteNodeData | null,
        };
    },
    computed: {
        graphVisible(): boolean {
            if (this.graphRenderLoading) {
                return true;
            }
            return this.tracerouteMode === "mac"
                ? this.macTracerouteOptions.rendered
                : this.vlanTracerouteOptions.rendered;
        },
        graphMaximized(): boolean {
            return this.vlanTracerouteOptions.maximized || this.macTracerouteOptions.maximized;
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
    },
    unmounted() {
        this.cancelOngoingTraceroute();
        this.vlanNetwork.cancelRender();
        this.macNetwork.cancelRender();
    },
    methods: {
        setTracerouteMode(mode: TracerouteMode) {
            if (this.tracerouteMode !== mode) {
                this.vlanTracerouteOptions.maximized = false;
                this.macTracerouteOptions.maximized = false;
                this.closeTracerouteNodePopup();
            }
            this.tracerouteMode = mode;
        },
        updateVlanTracerouteOption(key: keyof VlanTracerouteOptions, value: string | number | boolean) {
            (this.vlanTracerouteOptions[key] as string | number | boolean) = value;
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
            this.vlanAbortController?.abort();
            this.vlanAbortController = null;
            this.macAbortController?.abort();
            this.macAbortController = null;
            this.vlanNetwork.cancelRender();
            this.macNetwork.cancelRender();
            this.vlanTracerouteStarted = false;
            this.macTracerouteStarted = false;
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
        /**
         * Отправляем на сервер запрос трассировки указанного в поле для ввода VLAN.
         * И создаем в определенном блоке граф для данной трассировки.
         */
        load_traceroute() {
            if (this.tracerouteMode === "vlan" && !this.input.vlan) return;

            this.cancelOngoingTraceroute();
            this.closeTracerouteNodePopup();
            const requestId = ++this.activeRenderRequestId;
            this.vlanTracerouteStarted = true;
            this.startGraphRenderProgress();
            const controller = new AbortController();
            this.vlanAbortController = controller;

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
            }

            const deviceNameFilter = this.vlanTracerouteOptions.deviceNameFilter.trim();
            if (deviceNameFilter) {
                params.append("device_name", deviceNameFilter);
            }
            const groupFilter = this.vlanTracerouteOptions.groupFilter.trim();
            if (groupFilter) {
                params.append("group", groupFilter);
            }

            api.get("/api/v1/tools/traceroute?" + params.toString(), { signal: controller.signal })
                .then(async (resp) => {
                    if (requestId !== this.activeRenderRequestId) {
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
        toggleMaximizeVlanTraceroute() {
            this.vlanTracerouteOptions.maximized = !this.vlanTracerouteOptions.maximized;
            if (this.vlanTracerouteOptions.maximized) {
                setTimeout(() =>
                    document.getElementById("vlan-network")?.scrollIntoView({ behavior: "instant", block: "end" })
                );
            }
        },
        toggleMaximizeMACTraceroute() {
            this.macTracerouteOptions.maximized = !this.macTracerouteOptions.maximized;
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

            this.cancelOngoingTraceroute();
            this.closeTracerouteNodePopup();
            const requestId = ++this.activeRenderRequestId;
            this.macTracerouteStarted = true;
            this.startGraphRenderProgress();
            const controller = new AbortController();
            this.macAbortController = controller;
            const params: any = {
                mode: "mac",
                mac: validMac,
                ep: this.vlanTracerouteOptions.showEmptyPorts,
                ad: this.vlanTracerouteOptions.adminDownPorts,
                graph_min_length: this.vlanTracerouteOptions.graphMinLength,
                nodes_only: this.vlanTracerouteOptions.nodesOnly,
            };
            if (this.macTracerouteOptions.vlanFilter) {
                params.mac_vlan = this.macTracerouteOptions.vlanFilter;
            }
            const deviceNameFilter = this.vlanTracerouteOptions.deviceNameFilter.trim();
            if (deviceNameFilter) {
                params.device_name = deviceNameFilter;
            }
            const groupFilter = this.vlanTracerouteOptions.groupFilter.trim();
            if (groupFilter) {
                params.group = groupFilter;
            }

            api.get("/api/v1/tools/traceroute", { params: params, signal: controller.signal })
                .then(async (resp) => {
                    if (requestId !== this.activeRenderRequestId) {
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
        tracerouteMACWithVlanFilter(vlan: number) {
            this.macTracerouteOptions.vlanFilter = this.macTracerouteOptions.vlanFilter === vlan ? null : vlan;
            this.load_mac_traceroute();
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
