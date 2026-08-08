import api from "@/services/api";

/** Возвращает имена устройств, доступных для GPON. */
export async function getGponDeviceNames(): Promise<string[]> {
    const response = await api.get<string[]>("/api/v1/gpon/devices-names");
    return response.data;
}

/** Возвращает имена портов выбранного устройства. */
export async function getGponPortNames(deviceName: string): Promise<string[]> {
    const response = await api.get<string[]>(`/api/v1/gpon/ports-names/${encodeURIComponent(deviceName)}`);
    return response.data;
}
