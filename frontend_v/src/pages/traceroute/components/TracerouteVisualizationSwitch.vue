<template>
    <section
        class="rounded-4xl border border-gray-200/70 bg-white/80 p-3 backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/45"
    >
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
                <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">Визуализация</div>
                <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    Граф связей или географическая карта по координатам Zabbix
                </div>
            </div>
            <div
                class="grid w-full grid-cols-2 rounded-2xl border border-gray-200/80 bg-gray-100/80 p-1 dark:border-gray-700/60 dark:bg-gray-950/40 sm:w-fit"
            >
                <button
                    type="button"
                    :class="
                        modelValue === 'graph'
                            ? 'bg-white text-gray-900 shadow-sm dark:bg-gray-800 dark:text-gray-100'
                            : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100'
                    "
                    class="cursor-pointer rounded-xl px-3 py-2 text-sm font-medium transition"
                    @click="$emit('update:modelValue', 'graph')"
                >
                    Граф
                </button>
                <button
                    type="button"
                    :class="
                        modelValue === 'map'
                            ? 'bg-white text-gray-900 shadow-sm dark:bg-gray-800 dark:text-gray-100'
                            : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100'
                    "
                    class="cursor-pointer rounded-xl px-3 py-2 text-sm font-medium transition"
                    @click="$emit('update:modelValue', 'map')"
                >
                    Карта
                </button>
            </div>
        </div>
    </section>
</template>

<script setup lang="ts">
import type { TracerouteVisualizationMode } from "./types";

defineProps<{
    modelValue: TracerouteVisualizationMode;
}>();

defineEmits<{
    "update:modelValue": [value: TracerouteVisualizationMode];
}>();
</script>
