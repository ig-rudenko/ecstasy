import type { GponAddress } from "@/types/gpon/address";

/** Тип оконечного GPON-объекта. */
export const End3Type = {
    splitter: "splitter",
    rizer: "rizer",
} as const;

/** Supported endpoint type value. */
export type End3Type = (typeof End3Type)[keyof typeof End3Type];

/** Состояние порта технической возможности. */
export const TechCapabilityStatus = {
    active: "active",
    reserved: "reserved",
    pause: "pause",
    empty: "empty",
    bad: "bad",
} as const;

/** Supported technical capability status value. */
export type TechCapabilityStatus = (typeof TechCapabilityStatus)[keyof typeof TechCapabilityStatus];

/** Краткие данные абонента, занимающего порт. */
export interface SubscriberShortInfo {
    connectionID: number;
    customerID: number;
    customerName: string;
    transit: number;
}

/** Порт сплиттера или волокно райзера. */
export interface TechCapability {
    id: number;
    status: TechCapabilityStatus;
    number: number;
    subscribers: SubscriberShortInfo[];
    subscriber?: SubscriberShortInfo[];
}

/** Сплиттер или райзер вместе с доступными портами. */
export interface End3WithCapability {
    id: number;
    address: GponAddress;
    capacity: number;
    location: string;
    type: End3Type;
    capability: TechCapability[];
    detailInfo?: TechCapability[] | null;
    errorStatus?: number | string | null;
    errorMessage?: string | null;
}

/** Состояние OLT-порта. */
export interface OltState {
    id: number;
    deviceName: string;
    devicePort: string;
    fiber: string | null;
    description: string | null;
}

/** Состояние подключения строения к OLT. */
export interface HouseOltState {
    id: number;
    entrances: string | null;
    description: string | null;
    customerLines: End3WithCapability[];
}

/** A building connection returned on an OLT port page. */
export interface OltStructure extends HouseOltState {
    address: GponAddress;
}

/** An OLT connection returned on a building page. */
export interface BuildingOltState extends HouseOltState {
    statement: OltState;
}

/** Строение в детальном представлении технических данных. */
export interface BuildingTechData extends GponAddress {
    oltStates: BuildingOltState[];
}

/** Детальные технические данные OLT-порта. */
export interface OltTechData extends OltState {
    structures: OltStructure[];
}

/** Сводка абонентской линии в таблице технических данных. */
export interface CustomerLineSummary {
    type: End3Type | null;
    count: number;
    typeCount: number | null;
}

/** Строка списка технических данных. */
export interface TechDataListItem {
    deviceName: string;
    devicePort: string;
    address: GponAddress;
    building_type: "building" | "house";
    building_id: number;
    entrances: string | null;
    customerLine: CustomerLineSummary;
}

/** Фильтры списка технических данных. */
export interface TechDataListQuery {
    page: number;
    page_size: number;
    region: string;
    settlement: string;
    planStructure: string;
    street: string;
    house: string;
    block: string;
    deviceName: string;
    devicePort: string;
}

/** Filters used to find available endpoint capabilities. */
export interface End3CapabilitySearchQuery {
    street: string;
    house: string;
    block: string;
    tech_capability_status: TechCapabilityStatus;
    page: number;
}

/** Новый оконечный объект в форме создания технических данных. */
export interface End3CreateItem {
    address: GponAddress | null;
    buildAddress: boolean;
    location: string;
}

/** Данные формы создания технической возможности. */
export interface CreateTechDataPayload {
    oltState: Omit<OltState, "id">;
    houseB: {
        entrances: string;
        description: string;
        address: GponAddress | null;
    };
    end3: {
        type: End3Type;
        list: End3CreateItem[];
        existingSplitter: End3WithCapability | null;
        portCount: number;
    };
}

/** Данные добавления оконечного объекта к строению. */
export interface AddEnd3Payload {
    end3: CreateTechDataPayload["end3"];
    houseOltStateID: number;
}
