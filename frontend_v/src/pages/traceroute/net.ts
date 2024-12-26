import "vis-network/dist/dist/vis-network.min.css";


const baseVisOptions = {
    height: '900',
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

class TracerouteNetwork {
    private readonly elemID: string
    public options: any

    constructor(elementId: string) {
        this.elemID = elementId
        this.options = baseVisOptions
    }

    private textToDiv(html: string): HTMLDivElement {
        const container = document.createElement("div");
        container.innerHTML = html;
        return container;
    }


    async renderVisualData(nodes: Array<any>, edges: Array<any>) {
        const { Network } = await import("vis-network");
        new Network(
            (<HTMLDivElement>document.getElementById(this.elemID)),
            {
                nodes: nodes.map(value => {return {...value, title: this.textToDiv(value.title)}}),
                edges: edges.map(value => {return {...value, title: this.textToDiv(value.title)}})
            },
            this.options
        );
    }
}


export default TracerouteNetwork