import { ref } from "vue";

import api from "@/services/api";

interface PermissionResponse {
    permissions: string[];
    console: string | null;
}

class Permissions {
    private perms = ref<PermissionResponse>({
        permissions: [],
        console: null,
    });

    constructor() {
        this.load();

        api.get<PermissionResponse>("/api/v1/accounts/myself/permissions").then((value) => {
            const samePermissions =
                value.data.permissions.length === this.perms.value.permissions.length &&
                this.perms.value.permissions.every((p, i) => p === value.data.permissions[i]);

            if (!samePermissions || this.perms.value.console !== value.data.console) {
                this.perms.value = value.data;
                this.save();
            }
        });
    }

    private save() {
        localStorage.setItem("permissions", JSON.stringify(this.perms.value));
    }

    private load() {
        const permissions = localStorage.getItem("permissions");
        if (permissions) this.perms.value = JSON.parse(permissions);
    }

    has(permission: string): boolean {
        return this.perms.value.permissions.includes(permission);
    }

    hasConsoleAccess(): boolean {
        return this.perms.value.console !== null;
    }

    getConsoleUrl(): string | null {
        return this.perms.value.console;
    }

    hasGPONAnyPermission(): boolean {
        return this.perms.value.permissions.find((permission) => permission.startsWith("gpon")) !== undefined;
    }

    hasBulkDeviceCommandExecutePermission(): boolean {
        return this.has("auth.access_bulk_device_cmd");
    }

    getAll(): string[] {
        return [...this.perms.value.permissions];
    }

    getServiceAccess(): { key: string; label: string; enabled: boolean }[] {
        return [
            { key: "console", label: "Консоль", enabled: this.hasConsoleAccess() },
            { key: "discovery", label: "Discovery", enabled: this.has("auth.access_discovery") },
            { key: "maps", label: "Карты", enabled: this.has("auth.can_view_maps") },
            { key: "search", label: "Поиск", enabled: this.has("auth.access_desc_search") },
            { key: "traceroute", label: "Трассировка", enabled: this.has("auth.access_traceroute") },
            { key: "wtf", label: "WTF", enabled: this.has("auth.access_wtf_search") },
            {
                key: "rings",
                label: "Кольца",
                enabled: this.has("auth.access_rings") || this.has("auth.access_transport_rings"),
            },
            { key: "gpon", label: "GPON", enabled: this.hasGPONAnyPermission() },
            {
                key: "bulk_device_commands",
                label: "Массовые команды",
                enabled: this.hasBulkDeviceCommandExecutePermission(),
            },
        ];
    }
}

const permissions = new Permissions();

export default permissions;
