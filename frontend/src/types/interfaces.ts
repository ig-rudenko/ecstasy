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

export default Interface
export {Interface, newInterface}
