<template>
    <section
        v-show="mode === 'mac'"
        class="rounded-4xl border border-gray-200/70 bg-white/80 p-4 backdrop-blur transition hover:-translate-y-0.5 hover:bg-linear-to-br hover:from-transparent hover:via-transparent hover:to-indigo-500/10 hover:shadow-md dark:border-gray-700/70 dark:bg-gray-900/45 sm:p-6"
    >
        <div class="flex flex-col gap-5">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">Traceroute</h2>

            <div
                class="rounded-3xl border border-gray-200/80 bg-gray-50/70 p-3 dark:border-gray-700/80 dark:bg-gray-800/40"
            >
                <div class="flex gap-2 items-end">
                    <div class="min-w-0">
                        <label
                            class="mb-1.5 block text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400"
                        >
                            MAC
                        </label>
                        <InputText
                            :model-value="input.mac"
                            placeholder="AA:BB:CC:DD:EE:FF"
                            class="w-full rounded-2xl! font-mono! bg-white/95! text-gray-900! dark:bg-gray-950/60! dark:text-gray-100! border-gray-200/80! dark:border-gray-700/60!"
                            @update:model-value="$emit('update:mac', String($event ?? ''))"
                            @keyup.enter="$emit('load')"
                        />
                    </div>
                    <div class="min-w-0">
                        <label
                            class="mb-1.5 block text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400"
                        >
                            Фильтр VLAN
                        </label>
                        <InputNumber
                            :model-value="macOptions.vlanFilter"
                            placeholder="не задан"
                            :min="1"
                            :max="4096"
                            class="block w-full"
                            input-class="!w-full rounded-2xl! text-center! font-mono! bg-white/95! dark:!bg-gray-950/60 !text-gray-900 dark:!text-gray-100 !border-gray-200/80 dark:!border-gray-700/60"
                            @update:model-value="$emit('update:mac-vlan-filter', $event as number | null)"
                        />
                    </div>
                    <Button
                        rounded
                        class="h-10 w-full rounded-xl! px-3! lg:w-auto"
                        :loading="started"
                        :disabled="started"
                        v-tooltip.bottom="'Построить граф'"
                        @click="$emit('load')"
                    >
                        <span class="inline-flex items-center justify-center gap-1.5">
                            <i class="pi pi-share-alt text-sm" />
                            <span class="hidden text-xs font-medium sm:inline">Построить</span>
                        </span>
                    </Button>
                </div>
            </div>

            <div class="flex flex-wrap gap-3">
                <label
                    for="macAdminDownPorts"
                    class="flex cursor-pointer items-center gap-3 rounded-2xl border border-gray-200/80 bg-gray-50/80 px-3 py-2 text-sm text-gray-700 dark:border-gray-700/80 dark:bg-gray-800/60 dark:text-gray-300"
                >
                    <ToggleSwitch
                        input-id="macAdminDownPorts"
                        :model-value="options.adminDownPorts"
                        @update:model-value="$emit('update:option', 'adminDownPorts', $event)"
                    />
                    <span>Указывать выключенные порты</span>
                </label>
                <label
                    for="macShowEmptyPorts"
                    class="flex cursor-pointer items-center gap-3 rounded-2xl border border-gray-200/80 bg-gray-50/80 px-3 py-2 text-sm text-gray-700 dark:border-gray-700/80 dark:bg-gray-800/60 dark:text-gray-300"
                >
                    <ToggleSwitch
                        input-id="macShowEmptyPorts"
                        :model-value="options.showEmptyPorts"
                        @update:model-value="$emit('update:option', 'showEmptyPorts', $event)"
                    />
                    <span>Показывать пустые порты</span>
                </label>
                <label
                    for="macNodesOnly"
                    class="flex cursor-pointer items-center gap-3 rounded-2xl border border-gray-200/80 bg-gray-50/80 px-3 py-2 text-sm text-gray-700 dark:border-gray-700/80 dark:bg-gray-800/60 dark:text-gray-300"
                >
                    <ToggleSwitch
                        input-id="macNodesOnly"
                        :model-value="options.nodesOnly"
                        @update:model-value="$emit('update:option', 'nodesOnly', $event)"
                    />
                    <span>Only network nodes</span>
                </label>
            </div>

            <div class="grid gap-3 lg:grid-cols-[auto_1fr_1fr] lg:items-end">
                <TracerouteCommonOptions
                    :options="options"
                    :show-nodes-only="false"
                    @update:option="(key, value) => $emit('update:option', key, value)"
                />
            </div>
        </div>
    </section>
</template>

<script setup lang="ts">
import TracerouteCommonOptions from "./TracerouteCommonOptions.vue";
import type { MacTracerouteOptions, TracerouteInput, TracerouteMode, VlanTracerouteOptions } from "./types";

defineProps<{
    mode: TracerouteMode;
    input: TracerouteInput;
    options: VlanTracerouteOptions;
    macOptions: MacTracerouteOptions;
    started: boolean;
}>();

defineEmits<{
    load: [];
    "update:mac": [value: string];
    "update:mac-vlan-filter": [value: number | null];
    "update:option": [key: keyof VlanTracerouteOptions, value: string | number | boolean];
}>();
</script>
