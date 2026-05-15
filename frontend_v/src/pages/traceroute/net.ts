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

    constructor(elementId: string) {
        this.elemID = elementId;
        this.options = baseVisOptions;
        this.onNodeClick = null;
        this.onRenderProgress = null;
        this.network = null;
        this.rawNodes = [];
    }

    setNodeClickHandler(handler: NodeClickHandler | null): void {
        this.onNodeClick = handler;
    }

    setRenderProgressHandler(handler: RenderProgressHandler | null): void {
        this.onRenderProgress = handler;
    }

    focusNodeByName(query: string): boolean {
        if (!this.network) {
            return false;
        }

        const normalizedQuery = query.trim().toLowerCase();
        if (!normalizedQuery) {
            return false;
        }

        const node = this.rawNodes.find((value) => {
            const id = String(value.id ?? "").toLowerCase();
            const label = String(value.label ?? "").toLowerCase();
            return id.includes(normalizedQuery) || label.includes(normalizedQuery);
        });
        if (!node) {
            return false;
        }

        this.network.selectNodes([node.id]);
        this.network.focus(node.id, {
            animation: {
                duration: 450,
                easingFunction: "easeInOutQuad",
            },
            locked: false,
            scale: 1.35,
        });
        return true;
    }

    async renderVisualData(nodes: Array<any>, edges: Array<any>, options: any = null) {
        this.onRenderProgress?.(5);
        const { Network } = await import("vis-network");
        this.onRenderProgress?.(15);

        this.rawNodes = nodes.map((value) => ({ ...value }));
        const normalizedNodes = this.rawNodes;
        this.onRenderProgress?.(30);

        const normalizedEdges = edges;
        this.network = new Network(
            <HTMLDivElement>document.getElementById(this.elemID),
            {
                nodes: normalizedNodes as any,
                edges: normalizedEdges as any,
            },
            mergeOptions(this.options, options)
        );
        this.network.on("stabilizationProgress", (params: any) => {
            const total = Math.max(params.total || 1, 1);
            const progress = 30 + Math.round((Math.min(params.iterations, total) / total) * 69);
            this.onRenderProgress?.(progress);
        });
        this.network.once("stabilized", () => {
            this.onRenderProgress?.(100);
        });
        this.network.once("afterDrawing", () => {
            this.onRenderProgress?.(100);
        });
        this.network.on("click", (params: any) => {
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
    }
}

export default TracerouteNetwork;
