<template>
    <div v-if="items.length" class="flex flex-wrap gap-2 py-1 font-mono text-sm">
        <div
            v-for="vlanInfo in items"
            :key="vlanInfo.vid"
            class="inline-flex overflow-hidden rounded-xl border border-gray-200/60 shadow-sm dark:border-gray-700/60"
        >
            <button
                type="button"
                class="cursor-pointer bg-indigo-500 py-1.5 pl-3 pr-2 font-medium text-white transition hover:bg-indigo-600 dark:bg-indigo-600 dark:hover:bg-indigo-500"
                v-tooltip.bottom="activeVlan === vlanInfo.vid ? 'Убрать фильтр' : `Фильтр по VLAN ${vlanInfo.vid}`"
                @click="$emit('select', vlanInfo.vid)"
            >
                vid: {{ vlanInfo.vid }}
            </button>
            <span
                v-tooltip.bottom="vlanInfo.description || 'Нет описания'"
                class="max-w-48 truncate bg-gray-100 px-2 py-1.5 text-gray-800 dark:bg-gray-700 dark:text-white"
            >
                {{ vlanInfo.name }}
            </span>
            <span
                v-tooltip.bottom="'Количество'"
                class="bg-white py-1.5 pl-2 pr-3 text-gray-900 dark:bg-gray-800 dark:text-gray-100"
            >
                {{ vlanInfo.count }}
            </span>
        </div>
    </div>
</template>

<script setup lang="ts">
import type { VlanCountInfo } from "./types";

defineProps<{
    items: VlanCountInfo[];
    activeVlan: number | null;
}>();

defineEmits<{
    select: [vlan: number];
}>();
</script>
