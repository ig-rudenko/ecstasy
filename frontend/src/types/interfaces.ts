import {InterfaceComment, newInterfaceCommentsList} from "./comments";

class Interface {
    constructor(
        public name: string,
        public status: string,
        public description: string,
        public vlans: Array<number> = [],
        public comments: Array<InterfaceComment> = [],
        public graphsLink: string = ""
    ) { }
}


function newInterface(data: any): Interface {
    let comments: Array<InterfaceComment> = []
    if (data.Comments) { comments = newInterfaceCommentsList(data.Comments) }

    let vlans: Array<number> = []
    if (data["VLAN's"]) { vlans = Array.from(data["VLAN's"]).map(Number) }

    return new Interface(data.Interface, data.Status, data.Description, vlans, comments, data.GraphsLink || "")
}

function newInterfacesList(data: Array<any>): Array<Interface> {
    let res: Array<Interface> = []
    for (const line of data) {
        res.push(newInterface(line))
    }
    return res
}


class InterfacesCount {
    constructor(
        public abons: number,
        public abonsDown: number,
        public abonsDownNoDesc: number,
        public abonsDownWithDesc: number,
        public abonsUp: number,
        public abonsUpNoDesc: number,
        public abonsUpWithDesc: number,
        public count: number,
    ) { }
}
function newInterfacesCount(data: any): InterfacesCount {
    return new InterfacesCount(
        data.abons,
        data.abons_down,
        data.abons_down_no_desc,
        data.abons_down_with_desc,
        data.abons_up,
        data.abons_up_no_desc,
        data.abons_up_with_desc,
        data.count
    )
}

export default Interface
export {Interface, newInterface, newInterfacesList, InterfacesCount, newInterfacesCount}
