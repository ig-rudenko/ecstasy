<template>
    <section
        v-show="mode !== 'mac'"
        class="rounded-4xl border border-gray-200/70 bg-white/80 p-4 backdrop-blur transition hover:-translate-y-0.5 hover:bg-linear-to-br hover:from-transparent hover:via-transparent hover:to-indigo-500/10 hover:shadow-md dark:border-gray-700/70 dark:bg-gray-900/45 sm:p-6"
    >
        <div class="flex flex-col gap-5">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">Traceroute</h2>

            <div
                class="rounded-3xl border border-gray-200/80 bg-gray-50/70 p-3 dark:border-gray-700/80 dark:bg-gray-800/40"
            >
                <div class="grid gap-3 lg:grid-cols-[minmax(10rem,14rem)_auto_minmax(0,1fr)] lg:items-end">
                    <div v-if="mode === 'vlan'" class="min-w-0">
                        <label
                            class="mb-1.5 block text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400"
                        >
                            VLAN
                        </label>
                        <InputNumber
                            :min="1"
                            :max="4096"
                            :model-value="input.vlan"
                            placeholder="100"
                            class="w-full"
                            input-class="h-10! !w-full !rounded-2xl !text-center !font-mono !text-lg !bg-white/95 dark:!bg-gray-950/60 !text-gray-900 dark:!text-gray-100 !border-gray-200/80 dark:!border-gray-700/60"
                            @update:model-value="(value) => $emit('update:vlan', value as number | null)"
                            @keyup.enter="$emit('load')"
                            @input="$emit('vlan-info', $event)"
                        />
                    </div>
                    <Button
                        rounded
                        class="h-10 w-full rounded-xl! px-3! lg:w-auto"
                        :loading="started"
                        v-tooltip.bottom="'Построить граф'"
                        @click="$emit('load')"
                    >
                        <span class="inline-flex items-center justify-center gap-1.5">
                            <i class="pi pi-share-alt text-sm" />
                            <span class="hidden text-xs font-medium sm:inline">Построить</span>
                        </span>
                    </Button>
                    <div
                        v-if="mode === 'vlan' && inputVlanInfo.name"
                        class="flex items-center gap-2 min-h-12 rounded-2xl border border-gray-200/80 bg-white/80 px-3 py-2 font-mono text-sm text-gray-700 dark:border-gray-700/80 dark:bg-gray-900/45 dark:text-gray-200"
                    >
                        <div class="truncate">{{ inputVlanInfo.name }}</div>
                        <div v-if="inputVlanInfo.description" class="truncate text-xs text-gray-500 dark:text-gray-400">
                            {{ inputVlanInfo.description }}
                        </div>
                    </div>
                </div>
            </div>

            <div class="flex flex-wrap gap-3">
                <label
                    for="adminDownPorts"
                    class="flex cursor-pointer items-center gap-3 rounded-2xl border border-gray-200/80 bg-gray-50/80 px-3 py-2 text-sm text-gray-700 dark:border-gray-700/80 dark:bg-gray-800/60 dark:text-gray-300"
                >
                    <ToggleSwitch
                        input-id="adminDownPorts"
                        :model-value="options.adminDownPorts"
                        @update:model-value="$emit('update:option', 'adminDownPorts', $event)"
                    />
                    <span>Указывать выключенные порты</span>
                </label>
                <label
                    for="showEmptyPorts"
                    class="flex cursor-pointer items-center gap-3 rounded-2xl border border-gray-200/80 bg-gray-50/80 px-3 py-2 text-sm text-gray-700 dark:border-gray-700/80 dark:bg-gray-800/60 dark:text-gray-300"
                >
                    <ToggleSwitch
                        input-id="showEmptyPorts"
                        :model-value="options.showEmptyPorts"
                        @update:model-value="$emit('update:option', 'showEmptyPorts', $event)"
                    />
                    <span>Показывать пустые порты</span>
                </label>
                <label
                    v-if="mode === 'vlan'"
                    for="doubleCheckVlan"
                    class="flex cursor-pointer items-center gap-3 rounded-2xl border border-gray-200/80 bg-gray-50/80 px-3 py-2 text-sm text-gray-700 dark:border-gray-700/80 dark:bg-gray-800/60 dark:text-gray-300"
                >
                    <ToggleSwitch
                        input-id="doubleCheckVlan"
                        :model-value="options.doubleCheckVlan"
                        @update:model-value="$emit('update:option', 'doubleCheckVlan', $event)"
                    />
                    <span>Двухстороннее соответствие VLAN на соседних портах</span>
                </label>
                <div
                    v-if="mode === 'vlan'"
                    class="flex min-w-[16rem] flex-col gap-1.5 rounded-2xl border border-gray-200/80 bg-gray-50/80 px-3 py-2 dark:border-gray-700/80 dark:bg-gray-800/60"
                >
                    <label for="maxPortVlansEnabled" class="flex cursor-pointer items-center justify-between gap-3">
                        <span class="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
                            Лимит VLAN на порту
                        </span>
                        <ToggleSwitch
                            input-id="maxPortVlansEnabled"
                            :model-value="options.maxPortVlansEnabled"
                            @update:model-value="$emit('update:option', 'maxPortVlansEnabled', $event)"
                        />
                    </label>
                    <InputNumber
                        v-if="options.maxPortVlansEnabled"
                        input-id="maxPortVlans"
                        :min="1"
                        :max="4096"
                        :model-value="options.maxPortVlans"
                        placeholder="3000"
                        class="w-full"
                        input-class="h-9! !w-full !rounded-xl !bg-white/95 dark:!bg-gray-950/60 !text-gray-900 dark:!text-gray-100 !border-gray-200/80 dark:!border-gray-700/60"
                        @update:model-value="$emit('update:option', 'maxPortVlans', $event as number | null)"
                    />
                    <span v-if="options.maxPortVlansEnabled" class="text-xs text-gray-500 dark:text-gray-400">
                        При включении порты выше лимита будут пропущены
                    </span>
                </div>
            </div>

            <div class="grid gap-3 lg:grid-cols-[auto_1fr_1fr_auto] lg:items-end">
                <TracerouteCommonOptions
                    :options="options"
                    :show-nodes-only="true"
                    @update:option="(key, value) => $emit('update:option', key, value)"
                />
            </div>
        </div>
    </section>
</template>

<script setup lang="ts">
import { InputNumberInputEvent } from "primevue";
import TracerouteCommonOptions from "./TracerouteCommonOptions.vue";
import type { TracerouteInput, TracerouteMode, VlanTracerouteOptions } from "./types";

defineProps<{
    mode: TracerouteMode;
    input: TracerouteInput;
    inputVlanInfo: { name: string; description: string };
    options: VlanTracerouteOptions;
    started: boolean;
}>();

defineEmits<{
    load: [];
    "vlan-info": [event: InputNumberInputEvent];
    "update:vlan": [value: number | null];
    "update:option": [key: keyof VlanTracerouteOptions, value: string | number | boolean | null];
}>();
</script>
