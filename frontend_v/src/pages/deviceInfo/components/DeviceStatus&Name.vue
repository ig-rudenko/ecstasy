<template>
    <div class="flex w-full flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
        <div class="flex flex-wrap items-center gap-4">
            <span
                v-if="status === 0"
                class="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-red-100 text-red-600 dark:bg-red-500/15 dark:text-red-300"
            >
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="28"
                    height="28"
                    fill="currentColor"
                    class="bi bi-x-circle-fill"
                    viewBox="0 0 16 16"
                >
                    <path
                        d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z"
                    ></path>
                </svg>
            </span>
            <span
                v-else-if="status !== 1"
                class="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-gray-100 text-gray-500 dark:bg-gray-500/15 dark:text-gray-300"
            >
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="28"
                    height="28"
                    fill="currentColor"
                    class="bi bi-question-circle"
                    viewBox="0 0 16 16"
                >
                    <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z" />
                    <path
                        d="M5.255 5.786a.237.237 0 0 0 .241.247h.825c.138 0 .248-.113.266-.25.09-.656.54-1.134 1.342-1.134.686 0 1.314.343 1.314 1.168 0 .635-.374.927-.965 1.371-.673.489-1.206 1.06-1.168 1.987l.003.217a.25.25 0 0 0 .25.246h.811a.25.25 0 0 0 .25-.25v-.105c0-.718.273-.927 1.01-1.486.609-.463 1.244-.977 1.244-2.056 0-1.511-1.276-2.241-2.673-2.241-1.267 0-2.655.59-2.75 2.286zm1.557 5.763c0 .533.425.927 1.01.927.609 0 1.028-.394 1.028-.927 0-.552-.42-.94-1.029-.94-.584 0-1.009.388-1.009.94z"
                    />
                </svg>
            </span>
            <span
                v-else
                class="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-300"
            >
                <span class="relative flex size-4">
                    <span
                        class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"
                    ></span>
                    <span class="relative inline-flex size-4 rounded-full bg-emerald-500"></span>
                </span>
            </span>

            <button
                type="button"
                class="cursor-pointer inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-gray-200/70 bg-white/80 text-gray-500 transition hover:text-indigo-600 dark:border-gray-700/70 dark:bg-gray-950/40 dark:text-gray-300 dark:hover:text-indigo-300"
                @click="toggleStatus"
            >
                <i class="pi pi-wrench text-lg" />
            </button>

            <div class="flex flex-col gap-4">
                <div class="flex flex-wrap items-center gap-3">
                    <div
                        class="text-2xl font-semibold tracking-tight text-gray-900 dark:text-gray-100 sm:text-3xl font-mono"
                    >
                        {{ device.name }}
                    </div>
                    <PinDevice :device="device" />
                </div>

                <div class="flex flex-wrap items-center gap-3">
                    <div
                        v-show="device.ip"
                        class="inline-flex items-center rounded-2xl bg-indigo-600 px-3.5 py-1.5 font-mono text-sm text-white sm:text-base"
                    >
                        {{ device.ip }}
                    </div>
                    <div class="relative">
                        <button
                            type="button"
                            class="cursor-pointer inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-gray-200/70 bg-white/80 text-gray-500 transition hover:text-indigo-600 dark:border-gray-700/70 dark:bg-gray-950/40 dark:text-gray-300 dark:hover:text-indigo-300"
                            @click="copyIP"
                        >
                            <i class="pi pi-clone" />
                        </button>
                        <span
                            v-if="copied"
                            class="absolute left-full top-1/2 z-10 ml-2 -translate-y-1/2 whitespace-nowrap rounded-xl bg-white px-3 py-2 text-xs shadow dark:bg-surface-800"
                        >
                            {{ copiedStatus || "Скопировано!" }}
                        </span>
                    </div>
                    <PinnedDevicesPopover :show-text="false" />
                </div>
            </div>
        </div>

        <div class="flex font-mono">
            <div class="flex flex-wrap lg:flex-col gap-1">
                <div
                    v-if="device.vendor"
                    class="text-xs inline-flex px-4 py-1 items-center justify-center rounded-2xl border border-gray-200/70 bg-white/80 text-gray-500 transition hover:text-indigo-600 dark:border-gray-700/70 dark:bg-gray-950/40 dark:text-gray-300 dark:hover:text-indigo-300"
                >
                    {{ device.vendor }}
                </div>
                <div
                    v-if="device.model"
                    class="text-xs inline-flex px-4 py-1 items-center justify-center rounded-2xl border border-gray-200/70 bg-white/80 text-gray-500 transition hover:text-indigo-600 dark:border-gray-700/70 dark:bg-gray-950/40 dark:text-gray-300 dark:hover:text-indigo-300"
                >
                    {{ device.model }}
                </div>
                <div
                    v-if="serialNumber"
                    class="text-xs inline-flex px-4 py-1 items-center justify-center rounded-2xl border border-gray-200/70 bg-white/80 text-gray-500 transition hover:text-indigo-600 dark:border-gray-700/70 dark:bg-gray-950/40 dark:text-gray-300 dark:hover:text-indigo-300"
                >
                    {{ serialNumber }}
                </div>
            </div>
        </div>
    </div>

    <ConfirmPopup />
    <Popover ref="deviceStatus">
        <div v-if="poolStatus" class="w-[min(30rem,calc(100vw-2rem))] text-sm">
            <div class="mb-3 flex items-center justify-between gap-3">
                <div>Лимит одновременных подключений</div>
                <Badge class="font-mono" :value="poolStatus.connectionPoolSize" />
            </div>
            <div class="mb-3 grid gap-2 rounded-xl bg-gray-50 p-3 dark:bg-white/5">
                <div class="flex items-center justify-between gap-3">
                    <span class="text-xs text-gray-500 dark:text-gray-400">Поиск интерфейсов</span>
                    <Badge class="font-mono uppercase" severity="secondary" :value="poolStatus.portScanProtocol" />
                </div>
                <div class="flex items-center justify-between gap-3">
                    <span class="text-xs text-gray-500 dark:text-gray-400">Command</span>
                    <Badge class="font-mono uppercase" severity="secondary" :value="poolStatus.commandProtocol" />
                </div>
            </div>
            <div
                v-if="poolStatus.error"
                class="mb-3 rounded-xl border border-red-200 bg-red-50 p-3 text-red-800 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200"
                role="alert"
            >
                <div class="mb-1 flex items-center gap-2 font-medium">
                    <i class="pi pi-exclamation-triangle" />
                    Ошибка подключения
                </div>
                <div class="font-mono text-xs">{{ poolStatus.error.type }}</div>
                <div class="mt-1 break-words">{{ poolStatus.error.message }}</div>
                <div class="mt-2 text-xs opacity-75">{{ formatDate(poolStatus.error.occurredAt) }}</div>
            </div>
            <div
                v-if="poolStatus.sshHostKeyChange"
                class="mb-3 rounded-xl border border-amber-300 bg-amber-50 p-3 text-amber-950 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-100"
            >
                <div class="mb-2 flex items-center gap-2 font-medium">
                    <i class="pi pi-key" />
                    Изменился SSH host key
                </div>
                <div class="mb-3 text-xs">
                    Порт {{ poolStatus.sshHostKeyChange.port }},
                    {{ formatDate(poolStatus.sshHostKeyChange.detectedAt) }}
                </div>
                <div class="space-y-3">
                    <div>
                        <div class="mb-1 text-xs font-medium uppercase tracking-wide opacity-70">Сохранённый ключ</div>
                        <div v-if="poolStatus.sshHostKeyChange.previousKeys.length" class="space-y-1">
                            <div
                                v-for="key in poolStatus.sshHostKeyChange.previousKeys"
                                :key="`${key.type}-${key.fingerprint}`"
                                class="rounded-lg bg-white/70 px-2 py-1 font-mono text-xs dark:bg-black/20"
                            >
                                <div>{{ key.type }}</div>
                                <div class="break-all">{{ key.fingerprint }}</div>
                            </div>
                        </div>
                        <div v-else class="text-xs opacity-75">Сохранённый ключ не найден</div>
                    </div>
                    <div>
                        <div class="mb-1 text-xs font-medium uppercase tracking-wide opacity-70">Новый ключ</div>
                        <div class="space-y-1">
                            <div
                                v-for="key in poolStatus.sshHostKeyChange.newKeys"
                                :key="`${key.type}-${key.fingerprint}`"
                                class="rounded-lg bg-white/70 px-2 py-1 font-mono text-xs dark:bg-black/20"
                            >
                                <div>{{ key.type }}</div>
                                <div class="break-all">{{ key.fingerprint }}</div>
                            </div>
                        </div>
                    </div>
                </div>
                <Button
                    v-if="isStaff"
                    class="mt-3"
                    :disabled="confirmKeyLoading"
                    :loading="confirmKeyLoading"
                    icon="pi pi-check"
                    label="Подтвердить новый ключ"
                    severity="warn"
                    size="small"
                    @click="confirmSSHHostKey"
                />
                <div v-else class="mt-3 text-xs opacity-75">
                    Подтверждение нового ключа доступно только сотрудникам.
                </div>
            </div>
            <template v-if="poolStatus.connections.length">
                <div class="pb-3">
                    Переподключиться
                    <Button
                        :disabled="resetPoolLoading"
                        :loading="resetPoolLoading"
                        icon="pi pi-sync"
                        severity="warn"
                        outlined
                        rounded
                        size="small"
                        @click="resetPool"
                    />
                </div>
                <div class="flex gap-2 flex-col">
                    <div
                        v-for="(connection, index) in poolStatus.connections"
                        :key="index"
                        class="flex items-center gap-2"
                    >
                        <span v-if="connection.active" class="relative flex size-3">
                            <span
                                class="absolute inline-flex h-full w-full animate-ping rounded-full bg-teal-400 opacity-75"
                            ></span>
                            <span class="relative inline-flex size-3 rounded-full bg-teal-500"></span>
                        </span>
                        <span v-else class="relative inline-flex size-3 rounded-full bg-red-500"></span>
                        <span class="flex-1">
                            Подключение {{ index + 1 }} {{ connection.active ? "активно" : "неактивно" }}
                        </span>
                        <Badge
                            class="font-mono uppercase"
                            severity="secondary"
                            :value="connection.protocol || 'неизвестен'"
                        />
                    </div>
                </div>
            </template>
            <div v-else>Нет подключений</div>
        </div>
        <div v-else-if="poolStatusLoading">Загрузка...</div>
    </Popover>
</template>

<script lang="ts">
import { defineComponent, PropType } from "vue";

import api from "@/services/api";
import pinnedDevices from "@/services/pinnedDevices";
import { Device } from "@/services/devices";
import { errorToast, successToast } from "@/services/my.toast";
import store from "@/store";
import PinDevice from "@/components/PinDevice.vue";
import PinnedDevicesPopover from "@/components/PinnedDevicesPopover.vue";
import Commands from "@/pages/deviceInfo/components/Commands.vue";

interface ConnectionError {
    type: string;
    message: string;
    occurredAt: string;
}

interface SSHKeyInfo {
    type: string;
    fingerprint: string;
}

interface SSHHostKeyChange {
    detectedAt: string;
    port: number;
    previousKeys: SSHKeyInfo[];
    newKeys: SSHKeyInfo[];
}

interface PoolStatus {
    connectionPoolSize: number;
    statuses: boolean[];
    connections: {
        active: boolean;
        protocol: string | null;
    }[];
    portScanProtocol: string;
    commandProtocol: string;
    error: ConnectionError | null;
    sshHostKeyChange: SSHHostKeyChange | null;
}

interface RootState {
    auth: {
        user: {
            isStaff: boolean;
        } | null;
    };
}

export default defineComponent({
    components: { Commands, PinnedDevicesPopover, PinDevice },
    props: {
        status: { required: true, type: Number },
        device: { required: true, type: Object as PropType<Device> },
        consoleUrl: { required: true, type: String },
        serialNumber: { required: false, type: String, default: "" },
    },
    data() {
        return {
            copied: false,
            copiedStatus: "",
            poolStatus: null as null | PoolStatus,
            poolStatusLoading: false,
            resetPoolLoading: false,
            confirmKeyLoading: false,
            poolStatusTimer: null as null | number,
        };
    },
    mounted(): any {
        this.poolStatusTimer = window.setInterval(async () => {
            if ((<any>this.$refs.deviceStatus).visible) {
                await this.getPoolStatus();
            }
        }, 1000);
    },
    unmounted(): any {
        if (this.poolStatusTimer) {
            clearInterval(this.poolStatusTimer);
            this.poolStatusTimer = null;
        }
    },
    computed: {
        pinnedDevices() {
            return pinnedDevices;
        },
        isStaff(): boolean {
            return Boolean((store.state as RootState).auth.user?.isStaff);
        },
    },
    methods: {
        formatDate(value: string): string {
            return new Date(value).toLocaleString("ru-RU");
        },

        async copyIP(): Promise<void> {
            this.copied = true;
            this.copiedStatus = "";

            try {
                if (!navigator.clipboard?.writeText) {
                    this.copiedStatus = "Копирование доступно только через HTTPS или localhost";
                    return;
                }

                await navigator.clipboard.writeText(this.device.ip);
                this.copiedStatus = "Скопировано!";
            } catch (err) {
                this.copiedStatus = "Браузер запретил доступ к буферу обмена";
                console.error("Could not copy text: ", err);
            } finally {
                window.setTimeout(() => (this.copied = false), 3000);
            }
        },

        toggleStatus(event: Event) {
            this.getPoolStatus();
            {
                (<any>this.$refs.deviceStatus).toggle(event);
            }
        },

        async getPoolStatus() {
            this.poolStatusLoading = true;
            try {
                const resp = await api.get<PoolStatus>(`/api/v1/devices/${this.device.name}/pool`);
                this.poolStatus = resp.data;
            } catch (e) {}
            this.poolStatusLoading = false;
        },

        async resetPool() {
            if (this.resetPoolLoading) return;

            this.resetPoolLoading = true;
            try {
                await api.delete(`/api/v1/devices/${this.device.name}/pool`);
            } catch (e) {}
            setTimeout(() => {
                this.resetPoolLoading = false;
            }, 3000);
        },

        confirmSSHHostKey(event: Event) {
            this.$confirm.require({
                target: event.currentTarget as HTMLElement,
                message: "Подтвердить новый SSH host key? Выполните это только после проверки fingerprint.",
                icon: "pi pi-exclamation-triangle",
                acceptLabel: "Подтвердить",
                rejectLabel: "Отмена",
                acceptClass: "p-button-warning p-button-sm",
                defaultFocus: "reject",
                accept: () => this.acceptSSHHostKey(),
            });
        },

        async acceptSSHHostKey() {
            if (this.confirmKeyLoading) return;

            this.confirmKeyLoading = true;
            try {
                await api.post(`/api/v1/devices/${this.device.name}/ssh-host-key`);
                successToast("SSH ключ подтверждён", "Новое подключение будет использовать подтверждённый ключ.");
                await this.getPoolStatus();
            } catch {
                errorToast("Ошибка подтверждения", "Не удалось подтвердить новый SSH ключ.");
            } finally {
                this.confirmKeyLoading = false;
            }
        },
    },
});
</script>
