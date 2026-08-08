import api from "@/services/api";
import type {
    BuildingAddressQuery,
    End3AddressQuery,
    End3WithCapability,
    GponAddress,
    GponPaginatedResponse,
} from "@/types/gpon";

/** Загружает страницу адресов строений с учётом поиска и OLT-порта. */
export async function getBuildingAddresses(query: BuildingAddressQuery): Promise<GponPaginatedResponse<GponAddress>> {
    const response = await api.get<GponPaginatedResponse<GponAddress>>("/api/v1/gpon/addresses/buildings", {
        params: query,
    });
    return response.data;
}

/** Загружает страницу сплиттеров и райзеров, доступных для подключения. */
export async function getEnd3Addresses(query: End3AddressQuery): Promise<GponPaginatedResponse<End3WithCapability>> {
    const response = await api.get<GponPaginatedResponse<End3WithCapability>>("/api/v1/gpon/addresses/end3", {
        params: query,
    });
    return response.data;
}
