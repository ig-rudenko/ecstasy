import api from "@/services/api";

export async function getProtectedImage(url: string): Promise<string> {
    try {
        const response = await api.get(url, {responseType: "blob"});
        return URL.createObjectURL(response.data);
    } catch (error) {
        console.error(error);
        return "";
    }
}
