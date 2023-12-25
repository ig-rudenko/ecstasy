import api_request from "../api_request";

class ScanStatus {
    running: boolean
    progress?: number
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
      api_request.get(this.statusURL)
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
        api_request.post(this.runURL)
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

export default ScanStatus