import {ref} from "vue";

import api from "@/services/api";


interface PermissionResponse {
    permissions: string[];
    console: string | null;
    ecstasy_loop_url: string | null;
}


class Permissions {
    private perms = ref<PermissionResponse>({
            permissions: [], console: null, ecstasy_loop_url: null
        }
    );

    constructor() {
        this.load();

        api.get<PermissionResponse>("/api/v1/accounts/myself/permissions")
            .then(value => {
                if (
                    value.data.permissions.length !== this.perms.value.permissions?.length &&
                    this.perms.value.permissions?.every((p, i) => p === value.data.permissions[i]) ||
                    this.perms.value.console !== value.data.console ||
                    this.perms.value.ecstasy_loop_url !== value.data.ecstasy_loop_url
                ) {
                    this.perms.value = value.data;
                    this.save();
                }
            })
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

    hasEcstasyLoopPermission(): boolean {
        return this.perms.value.ecstasy_loop_url !== null;
    }

    getEcstasyLoopUrl(): string | null {
        return this.perms.value.ecstasy_loop_url;
    }

    hasConsoleAccess(): boolean {
        return this.perms.value.console !== null;
    }

    getConsoleUrl(): string | null {
        return this.perms.value.console;
    }

    hasGPONAnyPermission(): boolean {
        return this.perms.value.permissions.find(permission => permission.startsWith("gpon")) !== undefined;
    }

}

const permissions = new Permissions();

export default permissions;
