import "vis-network/dist/dist/vis-network.min.css";


const baseVisOptions = {
    height: '100%',
    locale: 'ru',
    configure: {
        enabled: false
    },
    layout: {
        randomSeed: 12345
    },
    edges: {
        smooth: {
            enabled: true,
            type: "dynamic"
        },
        arrows: {
            middle: {
                enabled: true
            }
        },
    },
    interaction: {
        dragNodes: true,
        hideEdgesOnDrag: false,
        hideNodesOnDrag: false
    },
    physics: {
        enabled: true,
        repulsion: {
            centralGravity: 0.2,
            damping: 0.89,
            nodeDistance: 130,
            springConstant: 0.05,
            springLength: 200
        },
        solver: 'repulsion',
        stabilization: {
            enabled: true,
            fit: true,
            iterations: 1000,
            onlyDynamicEdges: false,
            updateInterval: 50
        }
    },
    nodes: {
        size: 14,
        font:{
            multi: true,
            color:'#eeeeee',
            size: 12
        }
    }
}

export interface TracerouteNodeData {
    id: string | number
    label?: string | number
    title?: string
    [key: string]: unknown
}

type NodeClickHandler = (node: TracerouteNodeData | null) => void

class TracerouteNetwork {
    private readonly elemID: string
    public options: any
    private onNodeClick: NodeClickHandler | null

    constructor(elementId: string) {
        this.elemID = elementId
        this.options = baseVisOptions
        this.onNodeClick = null
    }

    private textToDiv(html: string): HTMLDivElement {
        const container = document.createElement("div");
        container.innerHTML = html;
        return container;
    }

    setNodeClickHandler(handler: NodeClickHandler | null): void {
        this.onNodeClick = handler;
    }

    async renderVisualData(nodes: Array<any>, edges: Array<any>) {
        const { Network } = await import("vis-network");
        const rawNodes = nodes.map(value => ({...value}));
        const normalizedNodes = rawNodes.map(value => {
            return {
                ...value,
                title: typeof value.title === "string" ? this.textToDiv(value.title) : value.title
            };
        });
        const normalizedEdges = edges.map(value => {
            return {
                ...value,
                title: typeof value.title === "string" ? this.textToDiv(value.title) : value.title
            };
        });
        const network = new Network(
            (<HTMLDivElement>document.getElementById(this.elemID)),
            {
                nodes: normalizedNodes,
                edges: normalizedEdges
            },
            this.options
        );
        network.on("click", (params) => {
            if (!this.onNodeClick) {
                return;
            }
            if (!params.nodes.length) {
                this.onNodeClick(null);
                return;
            }

            const clickedNodeId = params.nodes[0];
            const clickedNode = rawNodes.find(node => node.id === clickedNodeId) || null;
            this.onNodeClick(clickedNode);
        });
    }
}


export default TracerouteNetwork
