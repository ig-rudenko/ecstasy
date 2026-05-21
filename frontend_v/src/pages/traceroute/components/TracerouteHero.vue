<template>
    <section
        class="relative overflow-hidden rounded-4xl border border-gray-200/70 bg-white/80 backdrop-blur transition hover:-translate-y-0.5 hover:bg-linear-to-br hover:from-transparent hover:via-transparent hover:to-indigo-500/10 hover:shadow-md dark:border-gray-700/70 dark:bg-gray-900/45"
    >
        <div
            class="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(99,102,241,0.14),transparent_25%),radial-gradient(circle_at_85%_20%,rgba(14,165,233,0.14),transparent_22%)]"
        />
        <div class="relative flex flex-col gap-6 p-5 sm:p-8 lg:flex-row lg:items-center lg:justify-between">
            <div>
                <h1 class="text-3xl font-semibold tracking-tight text-gray-900 dark:text-gray-100 sm:text-4xl">
                    Трассировка L2
                </h1>
                <p class="mt-3 max-w-3xl text-sm leading-7 text-gray-600 dark:text-gray-300 sm:text-base">
                    Построение графа по VLAN или по MAC
                </p>
            </div>

            <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
                <span class="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    Режим
                </span>
                <div
                    class="grid w-full grid-cols-3 rounded-2xl border border-gray-200/80 bg-gray-100/80 p-1 dark:border-gray-700/60 dark:bg-gray-950/40 sm:inline-flex sm:w-fit"
                >
                    <button
                        v-for="mode in modes"
                        :key="mode.value"
                        type="button"
                        :class="
                            modelValue === mode.value
                                ? 'shadow-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100'
                                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
                        "
                        class="cursor-pointer rounded-xl px-3 py-2 text-sm font-medium transition sm:px-4"
                        @click="$emit('update:modelValue', mode.value)"
                    >
                        {{ mode.label }}
                    </button>
                </div>
            </div>
        </div>
    </section>
</template>

<script setup lang="ts">
import type { TracerouteMode } from "./types";

defineProps<{
    modelValue: TracerouteMode;
}>();

defineEmits<{
    "update:modelValue": [value: TracerouteMode];
}>();

const modes: Array<{ value: TracerouteMode; label: string }> = [
    { value: "vlan", label: "VLAN" },
    { value: "mac", label: "MAC" },
    { value: "neighbors", label: "Neighbors" },
];
</script>
