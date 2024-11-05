import api from "@/services/api";
import {AxiosResponse} from "axios";
import {Ref, ref} from "vue";

export interface MACDetail {
    vendor: string;
    address: string;
}


class MacSearch {
    public lastSearch: Ref<MACDetail|null> = ref(null);
    public lastMac: Ref<string|null> = ref(null);
    public lastMacDetail: Ref<string|null> = ref(null);
    public dialogVisible: Ref<boolean> = ref(false);

    async searchMac(mac: string) {
        this.dialogVisible.value = true;
        this.lastMac.value = mac;
        this.lastSearch.value = null;
        this.getMacDetail(mac);
        try {
            const resp= await api.get<MACDetail>("/tools/api/mac-vendor/" + mac)
            this.lastSearch.value = resp.data;
        } catch (error) {
            this.lastSearch.value = "Не удалось определить"
        }
        return this.lastSearch.value;
    }

    async getMacDetail(mac: string) {
        this.lastMacDetail.value = null;
        try {
            const resp= await api.get<MACDetail>("/tools/api/ip-mac-info/" + mac);
            this.lastMacDetail.value = resp.data;
        } catch (error) {
            this.lastMacDetail.value = "Не удалось определить";
        }
        return this.lastMacDetail.value;
    }

}

const macSearch = new MacSearch();
export default macSearch;