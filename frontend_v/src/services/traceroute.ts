import api from "@/services/api";

class ScanStatus {
    running: boolean
    progress: number | null
    available: boolean
    private statusURL: string
    private runURL: string

    constructor(statusURL: string, runURL: string) {
        this.running = false
        this.progress = null
        this.available = false
        this.statusURL = statusURL
        this.runURL = runURL
    }

    checkScanStatus() {
      api.get(this.statusURL)
            .then(
                resp => {
                    if (!resp.data || !resp.data.status) {
                        this.available = true;
                        this.running = false;
                        this.progress = null;
                    } else {
                        this.available = false;
                        this.running = true;
                        this.progress = resp.data.progress;
                    }
                }
            )
            .catch(
                () => {
                    this.available = false;
                    this.running = false;
                    this.progress = null;
                }
            )
      setTimeout(this.checkScanStatus, 5000);
    }

    run_vlans_scan() {
        if (!this.available) return;
        api.post(this.runURL)
            .then(
                () => {
                    this.available = false;
                    this.running = true;
                }
            )
            .catch(
                () => {
                    this.available = false;
                    this.running = false;
                }
            )
    }

}

interface InputVlanInfo {
    name: string;
    description: string;
}

export async function getInputVlanInfo(vlan: number): Promise<InputVlanInfo> {
    const resp = await api.get<InputVlanInfo>("/tools/api/vlan-desc?vlan="+vlan)
    return resp.data
}


export default ScanStatus