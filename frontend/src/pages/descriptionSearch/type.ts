import {InterfaceComment} from "../../types/comments";


export interface InterfaceMatchResult {
    device: string
    comments: Array<InterfaceComment>
    interface: {
        name: string
        status: string
        description: string
        vlans: string
        savedTime: string
        vlansSavedTime: string
    }
}

export interface MatchResult {
    interfaces: Array<InterfaceMatchResult>
}
