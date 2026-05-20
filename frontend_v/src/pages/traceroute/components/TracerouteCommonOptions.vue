<template>
    <div>
        <div class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
            Мин. число узлов
        </div>
        <InputGroup
            unstyled
            class="inline-flex h-12 w-full items-center rounded-2xl border border-gray-200/80 bg-white/90 px-1 dark:border-gray-700/60 dark:bg-gray-950/40 lg:w-auto"
        >
            <Button
                icon="pi pi-minus"
                text
                rounded
                @click="
                    options.graphMinLength > 1
                        ? $emit('update:option', 'graphMinLength', options.graphMinLength - 1)
                        : null
                "
            />
            <InputNumber
                :model-value="options.graphMinLength"
                :min="1"
                :max="100"
                input-class="!h-10 !w-full lg:!w-12 !border-0 !bg-transparent !text-center !font-mono !text-lg !text-gray-900 dark:!text-gray-100"
                @update:model-value="$emit('update:option', 'graphMinLength', Number($event || 1))"
            />
            <Button
                icon="pi pi-plus"
                text
                rounded
                @click="$emit('update:option', 'graphMinLength', options.graphMinLength + 1)"
            />
        </InputGroup>
    </div>
    <div class="min-w-0">
        <div class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
            Стартовое оборудование
        </div>
        <InputText
            :model-value="options.deviceNameFilter"
            placeholder="Имя оборудования"
            class="h-12 w-full rounded-2xl! bg-white/95! text-gray-900! dark:bg-gray-950/60! dark:text-gray-100! border-gray-200/80! dark:border-gray-700/60!"
            @update:model-value="$emit('update:option', 'deviceNameFilter', String($event ?? ''))"
        />
    </div>
    <div class="min-w-0">
        <div class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">Группа</div>
        <InputText
            :model-value="options.groupFilter"
            placeholder="Группа оборудования"
            class="h-12 w-full rounded-2xl! bg-white/95! text-gray-900! dark:bg-gray-950/60! dark:text-gray-100! border-gray-200/80! dark:border-gray-700/60!"
            @update:model-value="$emit('update:option', 'groupFilter', String($event ?? ''))"
        />
    </div>
    <label
        v-if="showNodesOnly"
        for="nodesOnly"
        class="flex cursor-pointer items-center gap-3 rounded-2xl border border-gray-200/80 bg-gray-50/80 px-3 py-2 text-sm text-gray-700 dark:border-gray-700/80 dark:bg-gray-800/60 dark:text-gray-300 lg:min-h-12"
    >
        <ToggleSwitch
            input-id="nodesOnly"
            :model-value="options.nodesOnly"
            @update:model-value="$emit('update:option', 'nodesOnly', $event)"
        />
        <span>Only network nodes</span>
    </label>
</template>

<script setup lang="ts">
import type { VlanTracerouteOptions } from "./types";

defineProps<{
    options: VlanTracerouteOptions;
    showNodesOnly: boolean;
}>();

defineEmits<{
    "update:option": [key: keyof VlanTracerouteOptions, value: string | number | boolean];
}>();
</script>
