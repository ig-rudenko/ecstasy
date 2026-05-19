import "vis-network/dist/dist/vis-network.min.css";

const baseVisOptions = {
    height: "100%",
    locale: "ru",
    configure: {
        enabled: false,
    },
    layout: {
        randomSeed: 12345,
    },
    edges: {
        smooth: {
            enabled: true,
            type: "dynamic",
        },
        arrows: {
            middle: {
                enabled: true,
            },
        },
    },
    interaction: {
        dragNodes: true,
        hideEdgesOnDrag: false,
        hideNodesOnDrag: false,
    },
    physics: {
        enabled: true,
        repulsion: {
            centralGravity: 0.2,
            damping: 0.89,
            nodeDistance: 130,
            springConstant: 0.05,
            springLength: 200,
        },
        solver: "repulsion",
        stabilization: {
            enabled: true,
            fit: true,
            iterations: 1000,
            onlyDynamicEdges: false,
            updateInterval: 50,
        },
    },
    nodes: {
        size: 14,
        font: {
            multi: true,
            color: "#eeeeee",
            size: 12,
        },
    },
};

function mergeOptions(baseOptions: any, overrideOptions: any): any {
    if (!overrideOptions || typeof overrideOptions !== "object") {
        return { ...baseOptions };
    }

    const result = { ...baseOptions };
    for (const [key, value] of Object.entries(overrideOptions)) {
        if (
            value &&
            typeof value === "object" &&
            !Array.isArray(value) &&
            typeof result[key] === "object" &&
            !Array.isArray(result[key])
        ) {
            result[key] = mergeOptions(result[key], value);
        } else {
            result[key] = value;
        }
    }
    return result;
}

function toTooltipHtmlElement(title: unknown): unknown {
    const tooltipRoot = document.createElement("div");
    if (typeof title === "string") {
        if (!title.trim()) {
            return title;
        }
        tooltipRoot.innerHTML = title;
    } else if (title && typeof title === "object") {
        const payload = title as Record<string, unknown>;
        if (payload.kind === "link") {
            const src = (payload.src ?? {}) as Record<string, unknown>;
            const dst = (payload.dst ?? {}) as Record<string, unknown>;
            const srcText = `${String(src.device ?? "")}:${String(src.port ?? "")}`;
            const dstText = `${String(dst.device ?? "")}:${String(dst.port ?? "")}`;
            tooltipRoot.innerHTML = `
                <div class="flex flex-col gap-1 min-w-72">
                    <div class="text-[11px] tracking-wide opacity-70 uppercase">SRC</div>
                    <div class="font-mono text-xs leading-5">${srcText}</div>
                    <div class="text-[11px] tracking-wide opacity-70 uppercase">DST</div>
                    <div class="font-mono text-xs leading-5">${dstText}</div>
                </div>
            `;
        } else if (payload.kind === "unknown_link") {
            const src = (payload.src ?? {}) as Record<string, unknown>;
            const srcText = `${String(src.device ?? "")}:${String(src.port ?? "")}`;
            const dstText = String(payload.destination_description ?? "");
            tooltipRoot.innerHTML = `
                <div class="flex flex-col gap-1 min-w-72">
                    <div class="text-[11px] tracking-wide opacity-70 uppercase">SRC</div>
                    <div class="font-mono text-xs leading-5">${srcText}</div>
                    <div class="text-[11px] tracking-wide opacity-70 uppercase">DESC</div>
                    <div class="font-mono text-xs leading-5">${dstText}</div>
                </div>
            `;
        } else if (payload.kind === "empty_port_link") {
            const src = (payload.src ?? {}) as Record<string, unknown>;
            const srcText = `${String(src.device ?? "")}:${String(src.port ?? "")}`;
            tooltipRoot.innerHTML = `
                <div class="flex flex-col gap-1 min-w-72">
                    <div class="text-[11px] tracking-wide opacity-70 uppercase">EMPTY PORT</div>
                    <div class="font-mono text-xs leading-5">${srcText}</div>
                </div>
            `;
        } else if (payload.kind === "mac_edge") {
            const from = (payload.from ?? {}) as Record<string, unknown>;
            const type = String(payload.mac_type ?? "none");
            const typeClass =
                type === "dynamic"
                    ? "bg-sky-600 text-white"
                    : type === "static"
                      ? "bg-zinc-600 text-white"
                      : type === "security"
                        ? "bg-amber-400 text-zinc-900"
                        : "bg-zinc-200 text-zinc-900";
            tooltipRoot.innerHTML = `
                <div class="flex flex-col gap-1 min-w-80 text-xs">
                    <div><span class="opacity-70">From:</span> <span class="font-mono">${String(from.device ?? "")}:${String(from.port ?? "")}</span></div>
                    <div><span class="opacity-70">To:</span> <span class="font-mono">${String(payload.to ?? "")}</span></div>
                    <div><span class="opacity-70">VLAN:</span> <span class="font-mono">${String(payload.vlan ?? "")}</span></div>
                    <div><span class="opacity-70">Type:</span> <span class="inline-block px-1.5 py-0.5 rounded ${typeClass}">${type}</span></div>
                    <div><span class="opacity-70">Detected:</span> ${String(payload.detected ?? "")}</div>
                </div>
            `;
        } else {
            return title;
        }
    } else {
        return title;
    }
    return tooltipRoot;
}

export interface TracerouteNodeData {
    id: string | number;
    label?: string | number;
    title?: string;
    [key: string]: unknown;
}

type NodeClickHandler = (node: TracerouteNodeData | null) => void;
type RenderProgressHandler = (progress: number) => void;

class TracerouteNetwork {
    private readonly elemID: string;
    public options: any;
    private onNodeClick: NodeClickHandler | null;
    private onRenderProgress: RenderProgressHandler | null;
    private network: any;
    private rawNodes: Array<TracerouteNodeData>;
    private rawEdges: Array<any>;
    private lastSearchQuery: string;
    private matchedNodeIds: Array<string | number>;
    private currentMatchIndex: number;
    private lastProgressEmitAt: number;
    private lastProgressValue: number;
    private renderSessionId: number;
    private physicsConfiguratorVisible: boolean;

    constructor(elementId: string) {
        this.elemID = elementId;
        this.options = baseVisOptions;
        this.onNodeClick = null;
        this.onRenderProgress = null;
        this.network = null;
        this.rawNodes = [];
        this.rawEdges = [];
        this.lastSearchQuery = "";
        this.matchedNodeIds = [];
        this.currentMatchIndex = -1;
        this.lastProgressEmitAt = 0;
        this.lastProgressValue = -1;
        this.renderSessionId = 0;
        this.physicsConfiguratorVisible = false;
    }

    private destroyNetwork(): void {
        if (!this.network) {
            return;
        }
        try {
            this.network.stopSimulation();
        } catch {
            // no-op
        }
        try {
            this.network.destroy();
        } catch {
            // no-op
        }
        this.network = null;
    }

    cancelRender(): void {
        this.renderSessionId += 1;
        this.destroyNetwork();
    }

    setPhysicsConfiguratorVisible(visible: boolean): void {
        this.physicsConfiguratorVisible = visible;
        if (!this.network) {
            return;
        }
        this.network.setOptions({
            configure: {
                enabled: visible,
                filter: (_option: string, path: string[]) => path.includes("physics"),
            },
        });
    }

    private applySearchOpacity(matchedNodeIds: Array<string | number>): void {
        if (!this.network?.body?.data?.nodes || !this.network?.body?.data?.edges) {
            return;
        }

        const matchedSet = new Set(matchedNodeIds);
        const nodeUpdates = this.rawNodes.map((node) => {
            if (!matchedNodeIds.length) {
                return { id: node.id, opacity: 1 };
            }
            return { id: node.id, opacity: matchedSet.has(node.id) ? 1 : 0.3 };
        });
        const edgeUpdates = this.network.body.data.edges.get().map((edge: any) => {
            const edgeOpacity =
                !matchedNodeIds.length || matchedSet.has(edge.from) || matchedSet.has(edge.to) ? 1 : 0.3;
            if (!edge.color) {
                return { id: edge.id, color: { opacity: edgeOpacity } };
            }
            if (typeof edge.color === "string") {
                return { id: edge.id, color: { color: edge.color, opacity: edgeOpacity } };
            }
            return {
                id: edge.id,
                color: {
                    ...edge.color,
                    opacity: edgeOpacity,
                },
            };
        });
        this.network.body.data.nodes.update(nodeUpdates);
        this.network.body.data.edges.update(edgeUpdates);
    }

    setNodeClickHandler(handler: NodeClickHandler | null): void {
        this.onNodeClick = handler;
    }

    setRenderProgressHandler(handler: RenderProgressHandler | null): void {
        this.onRenderProgress = handler;
    }

    focusNodeByName(query: string): { found: boolean; count: number; current: number } {
        if (!this.network) {
            return { found: false, count: 0, current: 0 };
        }

        const normalizedQuery = query.trim().toLowerCase();
        if (!normalizedQuery) {
            this.lastSearchQuery = "";
            this.matchedNodeIds = [];
            this.currentMatchIndex = -1;
            this.applySearchOpacity([]);
            return { found: false, count: 0, current: 0 };
        }

        if (normalizedQuery !== this.lastSearchQuery) {
            this.lastSearchQuery = normalizedQuery;
            this.matchedNodeIds = this.rawNodes
                .filter((value) => {
                    const id = String(value.id ?? "").toLowerCase();
                    const label = String(value.label ?? "").toLowerCase();
                    return id.includes(normalizedQuery) || label.includes(normalizedQuery);
                })
                .map((value) => value.id);
            this.currentMatchIndex = this.matchedNodeIds.length ? 0 : -1;
        } else if (this.matchedNodeIds.length) {
            this.currentMatchIndex = (this.currentMatchIndex + 1) % this.matchedNodeIds.length;
        }

        if (!this.matchedNodeIds.length || this.currentMatchIndex < 0) {
            this.applySearchOpacity([]);
            return { found: false, count: 0, current: 0 };
        }

        this.applySearchOpacity(this.matchedNodeIds);
        const nodeId = this.matchedNodeIds[this.currentMatchIndex];
        this.network.selectNodes([nodeId]);
        this.network.focus(nodeId, {
            animation: {
                duration: 450,
                easingFunction: "easeInOutQuad",
            },
            locked: false,
            scale: 1.35,
        });
        return {
            found: true,
            count: this.matchedNodeIds.length,
            current: this.currentMatchIndex + 1,
        };
    }

    async renderVisualData(nodes: Array<any>, edges: Array<any>, options: any = null): Promise<boolean> {
        this.renderSessionId += 1;
        const sessionId = this.renderSessionId;
        this.destroyNetwork();
        this.lastProgressEmitAt = 0;
        this.lastProgressValue = -1;
        this.onRenderProgress?.(5);
        const { Network } = await import("vis-network");
        if (sessionId !== this.renderSessionId) {
            return false;
        }
        this.onRenderProgress?.(15);

        this.rawNodes = nodes.map((value) => ({ ...value }));
        this.rawEdges = edges.map((value) => ({ ...value }));
        const normalizedNodes = this.rawNodes.map((value) => ({
            ...value,
            title: toTooltipHtmlElement(value?.title),
        }));
        this.onRenderProgress?.(30);

        const normalizedEdges = this.rawEdges.map((value) => ({
            ...value,
            title: toTooltipHtmlElement(value?.title),
        }));
        const nodesCount = normalizedNodes.length;
        const edgesCount = normalizedEdges.length;
        const isLargeGraph = nodesCount > 1200 || edgesCount > 2500;
        const renderOptions = mergeOptions(this.options, options);
        renderOptions.configure = {
            enabled: this.physicsConfiguratorVisible,
            filter: (_option: string, path: string[]) => path.includes("physics"),
        };

        if (isLargeGraph) {
            renderOptions.edges = mergeOptions(renderOptions.edges ?? {}, {
                smooth: { enabled: false },
            });
            renderOptions.interaction = mergeOptions(renderOptions.interaction ?? {}, {
                hideEdgesOnDrag: true,
            });
            renderOptions.physics = mergeOptions(renderOptions.physics ?? {}, {
                stabilization: {
                    updateInterval: 140,
                },
            });
        }

        // Give UI one frame to paint progress bar before heavy graph init.
        await new Promise<void>((resolve) => {
            requestAnimationFrame(() => resolve());
        });
        if (sessionId !== this.renderSessionId) {
            return false;
        }

        this.network = new Network(
            <HTMLDivElement>document.getElementById(this.elemID),
            {
                nodes: normalizedNodes as any,
                edges: normalizedEdges as any,
            },
            renderOptions
        );
        this.network.on("stabilizationProgress", (params: any) => {
            if (sessionId !== this.renderSessionId) {
                return;
            }
            const total = Math.max(params.total || 1, 1);
            const progress = 30 + Math.round((Math.min(params.iterations, total) / total) * 69);
            const now = performance.now();
            if (progress <= this.lastProgressValue) {
                return;
            }
            if (now - this.lastProgressEmitAt < 100 && progress < 99) {
                return;
            }
            this.lastProgressEmitAt = now;
            this.lastProgressValue = progress;
            this.onRenderProgress?.(progress);
        });
        this.network.once("stabilized", () => {
            if (sessionId !== this.renderSessionId) {
                return;
            }
            this.onRenderProgress?.(100);
        });
        this.network.once("afterDrawing", () => {
            if (sessionId !== this.renderSessionId) {
                return;
            }
            this.onRenderProgress?.(100);
        });
        this.network.on("click", (params: any) => {
            if (sessionId !== this.renderSessionId) {
                return;
            }
            if (!this.onNodeClick) {
                return;
            }
            if (!params.nodes.length) {
                this.onNodeClick(null);
                return;
            }

            const clickedNodeId = params.nodes[0];
            const clickedNode = this.rawNodes.find((node) => node.id === clickedNodeId) || null;
            this.onNodeClick(clickedNode);
        });
        return true;
    }
}

export default TracerouteNetwork;
