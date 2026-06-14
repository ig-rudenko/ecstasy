<script setup lang="ts">
import { computed } from "vue";
import { DiscoveryLookupItem } from "@/services/discovery";

type ProfileForm = {
    name: string;
    networks: string;
    excludeIps: string;
    deviceGroup: number | null;
    authGroups: number[];
    snmpCommunities: string;
    tryProtocols: string[];
    portScanProtocol: "snmp" | "telnet" | "ssh";
    cmdProtocol: "telnet" | "ssh";
    maxWorkers: number;
    timeoutSeconds: number;
    autoCreate: boolean;
    autoCreateMinConfidence: number;
    activateCreatedDevices: boolean;
    isActive: boolean;
};

const props = defineProps<{
    visible: boolean;
    isEditMode: boolean;
    creatingProfile: boolean;
    form: ProfileForm;
    deviceGroups: DiscoveryLookupItem[];
    authGroups: DiscoveryLookupItem[];
    protocolOptions: { label: string; value: string }[];
    portScanProtocolOptions: { label: string; value: "snmp" | "telnet" | "ssh" }[];
    cmdProtocolOptions: { label: string; value: "telnet" | "ssh" }[];
}>();

const emit = defineEmits<{
    (e: "update:visible", value: boolean): void;
    (e: "save"): void;
}>();

const modelVisible = computed({
    get: () => props.visible,
    set: (value: boolean) => emit("update:visible", value),
});
</script>

<template>
    <Dialog
        v-model:visible="modelVisible"
        modal
        maximizable
        :header="isEditMode ? 'Изменить discovery profile' : 'Новый discovery profile'"
        class="w-[min(96vw,980px)]"
    >
        <div class="grid gap-4 lg:grid-cols-2">
            <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                Имя
                <InputText v-model.trim="form.name" class="rounded-2xl" />
            </label>
            <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                Группа оборудования
                <Select
                    v-model="form.deviceGroup"
                    :options="deviceGroups"
                    optionLabel="name"
                    optionValue="id"
                    class="rounded-2xl"
                />
            </label>
            <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                Подсети
                <Textarea v-model="form.networks" rows="4" class="rounded-2xl" />
            </label>
            <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                Исключения
                <Textarea v-model="form.excludeIps" rows="4" class="rounded-2xl" />
            </label>
            <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                SNMP community
                <Textarea v-model="form.snmpCommunities" rows="4" class="rounded-2xl" />
                <span v-if="isEditMode" class="text-xs font-normal text-gray-500"
                    >Оставьте пустым, чтобы не менять сохраненные community.</span
                >
            </label>
            <div class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                Auth groups
                <div
                    class="grid max-h-34 gap-2 overflow-auto rounded-2xl border border-gray-200/80 p-3 dark:border-gray-700/80"
                >
                    <label
                        v-for="authGroup in authGroups"
                        :key="authGroup.id"
                        class="flex cursor-pointer items-center gap-2 text-sm font-normal"
                    >
                        <Checkbox v-model="form.authGroups" :value="authGroup.id" />
                        <span>{{ authGroup.name }}</span>
                    </label>
                </div>
            </div>
            <div class="grid gap-2 sm:grid-cols-2">
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
            <div class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                CLI protocols
                <div class="flex flex-wrap gap-3 rounded-2xl border border-gray-200/80 p-3 dark:border-gray-700/80">
                    <label
                        v-for="protocol in protocolOptions"
                        :key="protocol.value"
                        class="flex cursor-pointer items-center gap-2 text-sm font-normal"
                    >
                        <Checkbox v-model="form.tryProtocols" :value="protocol.value" />
                        <span>{{ protocol.label }}</span>
                    </label>
                </div>
            </div>
            <div class="grid gap-2 sm:grid-cols-3">
                <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                    Workers
                    <InputNumber
                        v-model="form.maxWorkers"
                        :min="1"
                        :max="80"
                        fluid
                        :useGrouping="false"
                        input-class="rounded-2xl"
                    />
                </label>
                <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                    Timeout
                    <InputNumber
                        v-model="form.timeoutSeconds"
                        :min="1"
                        :max="30"
                        fluid
                        :useGrouping="false"
                        input-class="rounded-2xl"
                    />
                </label>
                <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                    Confidence
                    <InputNumber
                        v-model="form.autoCreateMinConfidence"
                        :min="0"
                        :max="100"
                        fluid
                        :useGrouping="false"
                        input-class="rounded-2xl"
                    />
                </label>
            </div>
            <div
                class="flex flex-wrap flex-col gap-2 rounded-2xl border border-gray-200/80 p-3 dark:border-gray-700/80"
            >
                <label class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                    <ToggleSwitch v-model="form.isActive" />
                    Профиль активен
                </label>
                <label class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                    <ToggleSwitch v-model="form.autoCreate" />
                    Автосоздание
                </label>
                <label class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                    <ToggleSwitch v-model="form.activateCreatedDevices" />
                    Создавать оборудование активным
                </label>
            </div>
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
                :label="isEditMode ? 'Сохранить' : 'Создать'"
                icon="pi pi-check"
                class="rounded-2xl!"
                :loading="creatingProfile"
                @click="emit('save')"
            />
        </div>
    </Dialog>
</template>
