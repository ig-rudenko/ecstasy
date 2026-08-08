import api from "@/services/api";
import type { GponPermission } from "@/types/gpon";

/** Загружает Django permissions текущего пользователя для GPON. */
export async function getGponPermissions(): Promise<GponPermission[]> {
    const response = await api.get<GponPermission[]>("/api/v1/gpon/permissions");
    return response.data;
}

/** Проверяет наличие полного набора прав у пользователя. */
export function hasGponPermissions(current: GponPermission[], required: GponPermission[]): boolean {
    return required.every((permission) => current.includes(permission));
}
