import {ref} from "vue";
import {Device} from "@/services/devices.ts";

class PinnedDevices {
    public pinnedDevices = ref<Device[]>([]);

    constructor() {
        try {
            this.load();
        } catch (e) {
            console.error('Error loading pinned devices:', e);
        }
    }

    addDevice(device: Device) {
        if (!this.pinnedDevices.value.includes(device)) {
            this.pinnedDevices.value.push(device);
        }
        this.save();
    }

    removeDevice(device: Device) {
        console.log('Removing device from pinned list:', device);
        this.pinnedDevices.value = this.pinnedDevices.value.filter(d => d.ip !== device.ip);
        this.save();
    }

    clear() {
        this.pinnedDevices.value = [];
        this.save();
    }

    isPinned(deviceName: string) {
        try {
            return this.pinnedDevices.value.some(d => d.name === deviceName);
        } catch (e) {
            console.error('Error checking if device is pinned:', e);
            return false;
        }
    }

    save() {
        try {
            localStorage.setItem('pinnedDevices', JSON.stringify(this.pinnedDevices.value));
        } catch (e) {
            console.error('Error saving pinned devices:', e);
        }
    }

    load() {
        try {
            const savedDevices = localStorage.getItem('pinnedDevices');
            if (savedDevices) {
                this.pinnedDevices.value = JSON.parse(savedDevices);
            }
        } catch (e) {
            console.error('Error loading pinned devices from localStorage:', e);
        }
    }

}


const pinnedDevices = new PinnedDevices();
export default pinnedDevices;