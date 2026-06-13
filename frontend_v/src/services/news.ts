import api from "@/services/api";

export type GlobalNewsSeverity = "primary" | "secondary" | "success" | "warning" | "danger" | "info" | "light" | "dark";

export interface GlobalNews {
    id: number;
    title: string;
    content: string;
    severity: GlobalNewsSeverity;
    createdAt: string;
    expiredAt: string | null;
}

export async function getGlobalNews(): Promise<GlobalNews[]> {
    const response = await api.get<GlobalNews[]>("/api/v1/news/");
    return response.data;
}
