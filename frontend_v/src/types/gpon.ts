import {Address} from "@/types/address.ts";

export enum End3Type {
    splitter = "splitter",
    rizer = "rizer"
}

export interface SubscriberShortInfo {
    connectionID: number
    customerID: number
    customerName: string
    transit: number
}

export enum TechCapabilityStatus {
    active = "active",
    reserved = "reserved",
    pause = "pause",
    empty = "empty",
    bad = "bad"
}

export interface TechCapability {
    id: number
    status: TechCapabilityStatus,
    number: number
    subscriber: SubscriberShortInfo[]
}

export interface End3WithCapability {
    id: number
    address: Address
    capacity: number
    location: string
    type: End3Type
    capability: TechCapability[]
}
