import {Ref, ref} from "vue";

import api from "@/services/api";
import errorFmt from "@/errorFmt";
import {errorToast} from "@/services/my.toast";

interface MacAffiliation {
    mac: string
    device: string
    port: string
}

interface BrasData {
    BRAS1: {
        session: string
        errors: string[]
    }
    BRAS2: {
        session: string
        errors: string[]
    }
}

interface BrasCutSessionResult {
    errors: string[]
    portReloadStatus: string
}

class BrasSessionsService {
    public dialogVisible: Ref<boolean> = ref(false);
    private lastSessions: Ref<BrasData | null> = ref(null);
    public current: Ref<MacAffiliation | null> = ref(null);
    public cuttingNow: Ref<boolean> = ref(false)
    public cutSessionResult: Ref<BrasCutSessionResult | null> = ref(null);

    async getSessions(mac: string, deviceName: string, port: string) {
        this.lastSessions.value = null;
        this.current.value = {
            mac: mac,
            device: deviceName,
            port: port
        };
        this.dialogVisible.value = true;
        try {
            const resp = await api.get<BrasData>("/api/v1/devices/session?mac=" + mac)
            this.lastSessions.value = resp.data
        } catch (error: any) {
            errorToast("Ошибка", errorFmt(error))
        }
    }

    get currentMac() {
        return this.current.value?.mac;
    }

    get sessions() {
        return this.lastSessions.value;
    }

    async cutSession(reloadPort: boolean) {
        if (!this.current.value) return;
        this.cuttingNow.value = true
        let data = {
            device: reloadPort?this.current.value.device:'',
            port: reloadPort?this.current.value.port:'',
            mac: this.currentMac
        }
        try {
            const resp = await api.post<BrasCutSessionResult>("/api/v1/devices/cut-session", data)
            this.cutSessionResult.value = resp.data;
        } catch (error: any) {
            errorToast("Ошибка", errorFmt(error))
        }
        this.cuttingNow.value = false
    }

}

const brasSessionsService = new BrasSessionsService();
export default brasSessionsService;