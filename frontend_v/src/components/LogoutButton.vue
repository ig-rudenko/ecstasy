<script setup lang="ts">
import { ref } from "vue";
import { useStore } from "vuex";

import { isOIDCLogin } from "@/oidc";

const store = useStore();
const logoutVisible = ref(false);
const oidcLogin = isOIDCLogin();

async function logout(endKeycloakSession: boolean) {
    const redirectUrl = await store.dispatch("auth/logout", endKeycloakSession);
    location.href = redirectUrl;
}
</script>

<template>
    <Button
        v-tooltip.bottom="'Выйти'"
        icon="pi pi-sign-out"
        @click="logoutVisible = true"
        severity="secondary"
        class="shadow-sm rounded-2xl dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-100 dark:hover:bg-gray-600 bg-opacity-10"
        outlined
    />

    <Dialog
        v-model:visible="logoutVisible"
        modal
        pt:root:class="border-0 bg-surface-200 dark:bg-surface-800 rounded-xl p-2"
        pt:mask:class="backdrop-blur-sm"
    >
        <template #container="{ closeCallback }">
            <div class="p-4 text-xl font-semibold text-surface-800 dark:text-surface-200">
                Вы уверены, что хотите выйти?
            </div>
            <div class="flex flex-wrap justify-end gap-2 p-2">
                <Button
                    type="button"
                    label="Нет"
                    severity="secondary"
                    autofocus
                    @click="closeCallback"
                    class="rounded-2xl"
                />
                <Button
                    type="button"
                    :label="oidcLogin ? 'Только из Ecstasy' : 'Выйти'"
                    severity="danger"
                    outlined
                    @click="logout(false)"
                    class="rounded-2xl"
                />
                <Button
                    v-if="oidcLogin"
                    type="button"
                    label="Из Ecstasy и OIDC"
                    severity="danger"
                    @click="logout(true)"
                    class="rounded-2xl"
                />
            </div>
        </template>
    </Dialog>
</template>
