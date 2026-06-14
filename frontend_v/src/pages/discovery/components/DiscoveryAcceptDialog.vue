<script setup lang="ts">
import { computed } from "vue";
import { DiscoveryCandidate, DiscoveryLookupItem } from "@/services/discovery";

type AcceptForm = {
    name: string;
    deviceGroup: number | null;
    authGroup: number | null;
    cmdProtocol: "telnet" | "ssh";
    portScanProtocol: "snmp" | "telnet" | "ssh";
    snmpCommunity: string;
    collectInterfaces: boolean;
};

const props = defineProps<{
    visible: boolean;
    selectedCandidate: DiscoveryCandidate | null;
    form: AcceptForm;
    deviceGroups: DiscoveryLookupItem[];
    authGroups: DiscoveryLookupItem[];
    portScanProtocolOptions: { label: string; value: "snmp" | "telnet" | "ssh" }[];
    cmdProtocolOptions: { label: string; value: "telnet" | "ssh" }[];
}>();

const emit = defineEmits<{
    (e: "update:visible", value: boolean): void;
    (e: "accept"): void;
}>();

const modelVisible = computed({
    get: () => props.visible,
    set: (value: boolean) => emit("update:visible", value),
});

const authCheckFailed = computed(() => props.selectedCandidate?.authCheckStatus === "FAILED");
const authCheckSuccess = computed(() => props.selectedCandidate?.authCheckStatus === "SUCCESS");
</script>

<template>
    <Dialog
        v-model:visible="modelVisible"
        modal
        maximizable
        header="Принять кандидата"
        class="w-[min(96vw,820px)] w-fit"
    >
        <div v-if="selectedCandidate" class="grid gap-4">
            <div
                class="rounded-2xl border border-gray-200/80 bg-gray-50/80 p-4 dark:border-gray-700/80 dark:bg-gray-800/60"
            >
                <div class="font-mono text-sm text-gray-500">{{ selectedCandidate.ip }}</div>
                <div class="mt-1 text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {{ [selectedCandidate.vendor, selectedCandidate.model].filter(Boolean).join(" · ") || "Unknown" }}
                </div>
            </div>
            <Message v-if="authCheckFailed" severity="error" class="whitespace-pre font-mono">
                {{ selectedCandidate.authCheckError || "Не удалось подключиться с AuthGroup из профиля discovery." }}
            </Message>
            <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                Имя устройства
                <InputText v-model.trim="form.name" class="rounded-2xl" />
            </label>
            <div class="grid gap-4 sm:grid-cols-2">
                <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                    Группа оборудования
                    <Select
                        v-model="form.deviceGroup"
                        :options="deviceGroups"
                        optionLabel="name"
                        optionValue="id"
                        class="rounded-2xl"
                        :disabled="authCheckSuccess"
                    />
                </label>
                <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                    Auth group
                    <Select
                        v-model="form.authGroup"
                        :options="authGroups"
                        optionLabel="name"
                        optionValue="id"
                        class="rounded-2xl"
                    />
                </label>
            </div>
            <div class="grid gap-4 sm:grid-cols-2">
                <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                    Port scan
                    <Select
                        v-model="form.portScanProtocol"
                        :options="portScanProtocolOptions"
                        optionLabel="label"
                        optionValue="value"
                        class="rounded-2xl"
                    />
                </label>
                <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                    Command
                    <Select
                        v-model="form.cmdProtocol"
                        :options="cmdProtocolOptions"
                        optionLabel="label"
                        optionValue="value"
                        class="rounded-2xl"
                    />
                </label>
            </div>
            <div>
                <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                    SNMP community
                    <InputText v-model.trim="form.snmpCommunity" class="rounded-2xl" placeholder="******" />
                    <div class="text-xs text-muted">
                        Значение будет взято из discovery, если хотите заменить на своё, то укажите его здесь
                    </div>
                </label>
            </div>
            <label class="mt-3 flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                <ToggleSwitch v-model="form.collectInterfaces" />
                Первичный сбор интерфейсов
            </label>
        </div>

        <div class="mt-6 flex justify-end gap-2">
            <Button
                label="Отмена"
                icon="pi pi-times"
                severity="secondary"
                outlined
                class="rounded-2xl!"
                @click="modelVisible = false"
            />
            <Button
                label="Создать устройство"
                icon="pi pi-check"
                class="rounded-2xl!"
                :disabled="authCheckFailed"
                @click="emit('accept')"
            />
        </div>
    </Dialog>
</template>
