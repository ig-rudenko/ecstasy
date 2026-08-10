import api from "@/services/api";
import type {
    AddEnd3Payload,
    BuildingTechData,
    CreateTechDataPayload,
    End3CapabilitySearchQuery,
    End3WithCapability,
    GponPaginatedResponse,
    HouseOltState,
    OltState,
    OltTechData,
    TechCapability,
    TechDataListItem,
    TechDataListQuery,
} from "@/types/gpon";

/** Загружает пагинированный список технических данных. */
export async function getTechDataList(query: TechDataListQuery): Promise<GponPaginatedResponse<TechDataListItem>> {
    const response = await api.get<GponPaginatedResponse<TechDataListItem>>("/api/v1/gpon/tech-data", {
        params: query,
    });
    return response.data;
}

/** Создаёт технические данные OLT, строения и оконечных объектов. */
export async function createTechData(payload: CreateTechDataPayload): Promise<void> {
    await api.post("/api/v1/gpon/tech-data", payload);
}

/** Загружает технические данные выбранного OLT-порта. */
export async function getOltTechData(deviceName: string, devicePort: string): Promise<OltTechData> {
    const response = await api.get<OltTechData>(`/api/v1/gpon/tech-data/${encodeURIComponent(deviceName)}`, {
        params: { port: devicePort },
    });
    return response.data;
}

/** Загружает технические данные строения. */
export async function getBuildingTechData(buildingId: number): Promise<BuildingTechData> {
    const response = await api.get<BuildingTechData>(`/api/v1/gpon/tech-data/building/${buildingId}`);
    return response.data;
}

/** Finds endpoint capabilities matching an address and availability status. */
export async function getEnd3CapabilityList(
    query: End3CapabilitySearchQuery
): Promise<GponPaginatedResponse<End3WithCapability>> {
    const response = await api.get<GponPaginatedResponse<End3WithCapability>>("/api/v1/gpon/tech-data/end3", {
        params: query,
    });
    return response.data;
}
/** Loads one endpoint together with its ports. */
export async function getEnd3TechData(end3Id: number): Promise<End3WithCapability> {
    const response = await api.get<End3WithCapability>(`/api/v1/gpon/tech-data/end3/${end3Id}`);
    return response.data;
}

/** Добавляет сплиттер или райзер к состоянию строения. */
export async function addEnd3(payload: AddEnd3Payload): Promise<void> {
    await api.post("/api/v1/gpon/tech-data/end3", payload);
}

/** Обновляет адрес и параметры оконечного объекта. */
export async function updateEnd3(end3: End3WithCapability): Promise<End3WithCapability> {
    const response = await api.patch<End3WithCapability>(`/api/v1/gpon/tech-data/end3/${end3.id}`, end3);
    return response.data;
}

/** Удаляет оконечный объект. */
export async function deleteEnd3(end3Id: number): Promise<void> {
    await api.delete(`/api/v1/gpon/tech-data/end3/${end3Id}`);
}

/** Обновляет состояние отдельного порта технической возможности. */
export async function updateTechCapability(capability: TechCapability): Promise<TechCapability> {
    const response = await api.patch<TechCapability>(
        `/api/v1/gpon/tech-data/tech-capability/${capability.id}`,
        capability
    );
    return response.data;
}

/** Обновляет параметры OLT-порта. */
export async function updateOltState(oltState: OltState): Promise<OltState> {
    const response = await api.put<OltState>(`/api/v1/gpon/tech-data/olt-state/${oltState.id}`, oltState);
    return response.data;
}

/** Обновляет параметры подключения строения к OLT. */
export async function updateHouseOltState(houseOltState: HouseOltState): Promise<HouseOltState> {
    const response = await api.put<HouseOltState>(
        `/api/v1/gpon/tech-data/house-olt-state/${houseOltState.id}`,
        houseOltState
    );
    return response.data;
}
