/** Тип строения, используемый в GPON-формах и ответах API. */
export type GponBuildingType = "building" | "house";

/** Адрес GPON-объекта в формате backend API. */
export interface GponAddress {
    id?: number;
    building_id?: number;
    region: string;
    settlement: string;
    planStructure: string;
    street: string;
    house: string;
    block: number | null;
    floor?: number | null;
    apartment?: number | null;
    building_type?: GponBuildingType;
    floors?: number;
    total_entrances?: number;
}

/** Параметры поиска адресов строений. */
export interface BuildingAddressQuery {
    page: number;
    page_size: number;
    search?: string;
    device?: string;
    port?: string;
}

/** Параметры поиска сплиттеров и райзеров по адресу. */
export interface End3AddressQuery {
    page: number;
    page_size: number;
    search?: string;
    address_id?: number;
}
