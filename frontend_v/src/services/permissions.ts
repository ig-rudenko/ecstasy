import {ref} from "vue";

import api from "@/services/api";


class Permissions {
    private perms = ref<string[]>([]);

    constructor() {
        this.load();

        api.get<{ permissions: string[] }>("/api/accounts/myself/permissions")
            .then(value => {
                if (value.data.permissions.length !== this.perms.value.length &&
                    this.perms.value.every((p, i) => p === value.data.permissions[i])
                ) {
                    this.perms.value.push(...value.data.permissions)
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
        return this.perms.value.includes(permission);
    }

    hasGPONAnyPermission(): boolean {
        return this.perms.value.find(permission => permission.startsWith("gpon")) !== undefined;
    }

}

const permissions = new Permissions();

export default permissions;
