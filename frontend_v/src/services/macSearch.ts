import {Ref, ref} from "vue";

import api from "@/services/api";

export interface MACDetail {
    vendor: string;
    address: string;
}


export interface IPMACInfoResult {
    info: {
        device: {
            name: string;
            ip: string;
        };
        results: {
            mac: string;
            ip: string;
            vlan: string;
            device_name: string;
            port: string;
        }[]
    }[];
    zabbix: {
        name: string;
        hostid: string;
    }[];
    zabbix_url: string;
}


class MacSearch {
    public lastSearch: Ref<MACDetail | null> = ref(null);
    public lastMac: Ref<string | null> = ref(null);
    public lastMacDetail: Ref<IPMACInfoResult | null> = ref(null);
    public dialogVisible: Ref<boolean> = ref(false);

    async searchMac(mac: string) {
        this.dialogVisible.value = true;
        this.lastMac.value = mac;
        this.lastSearch.value = null;
        this.getMacDetail(mac);
        try {
            const resp = await api.get<MACDetail>("/api/v1/tools/mac-vendor/" + mac)
            this.lastSearch.value = resp.data;
        } catch (error) {
            this.lastSearch.value = {
                vendor: "Не удалось определить",
                address: "Не удалось определить"
            }
        }
        return this.lastSearch.value;
    }

    async getMacDetail(mac: string) {
        this.dialogVisible.value = true;
        this.lastMacDetail.value = null;
        try {
            const resp = await api.get<IPMACInfoResult>("/api/v1/tools/ip-mac-info/" + mac);
            this.lastMacDetail.value = resp.data;
        } catch (error) {
            this.lastMacDetail.value = null;
        }
        return this.lastMacDetail.value;
    }

}

const macSearch = new MacSearch();
export default macSearch;