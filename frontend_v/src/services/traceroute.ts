import api from "@/services/api";

interface InputVlanInfo {
    name: string;
    description: string;
}

export async function getInputVlanInfo(vlan: number): Promise<InputVlanInfo> {
    const resp = await api.get<InputVlanInfo>("/api/v1/tools/vlan-desc?vlan=" + vlan);
    return resp.data;
}
