<template>
    <section
        class="relative min-h-120 overflow-hidden rounded-4xl border border-gray-700 bg-neutral-950 shadow-inner"
        :class="maximized ? 'overflow-visible! rounded-none! border-0 shadow-none min-h-0 bg-transparent' : ''"
    >
        <div
            v-show="mode !== 'mac'"
            :class="['relative h-150 min-h-120 sm:h-225', vlanMaximized ? 'maximized-shell' : '']"
        >
            <div v-if="vlanRendered" class="absolute! top-3 right-30 left-3 z-101 flex items-center gap-2 sm:left-auto">
                <InputText
                    :model-value="graphNodeSearch"
                    placeholder="Node"
                    class="w-full rounded-xl! bg-white/95! text-gray-900! dark:bg-gray-950/80! dark:text-gray-100! border-gray-200/80! dark:border-gray-700/60! sm:w-44!"
                    @update:model-value="$emit('update:graphNodeSearch', String($event ?? ''))"
                    @keyup.enter="$emit('focus-node')"
                />
                <Button
                    icon="pi pi-search"
                    rounded
                    severity="secondary"
                    v-tooltip.bottom="'Найти узел'"
                    @click="$emit('focus-node')"
                />
                <span
                    v-if="graphSearchMatchesCount > 0"
                    class="rounded-lg bg-black/60 px-2 py-1 font-mono text-xs text-white"
                >
                    {{ graphSearchMatchIndex }}/{{ graphSearchMatchesCount }}
                </span>
            </div>
            <Button
                v-if="vlanRendered"
                class="absolute! z-101 top-3 right-18"
                icon="pi pi-sliders-h"
                rounded
                severity="secondary"
                v-tooltip.bottom="physicsMenuVisible ? 'Скрыть настройки физики' : 'Показать настройки физики'"
                @click="$emit('toggle-physics')"
            />
            <Button
                v-if="vlanRendered"
                class="absolute! z-101 top-3 right-6"
                :icon="vlanMaximized ? 'pi pi-arrow-down-left-and-arrow-up-right-to-center' : 'pi pi-expand'"
                rounded
                severity="secondary"
                v-tooltip.bottom="vlanMaximized ? 'Выйти из полного экрана' : 'На весь экран'"
                @click="$emit('toggle-maximize-vlan')"
            />
            <div
                v-if="graphRenderLoading && mode !== 'mac'"
                class="absolute! z-102 left-3 right-3 top-16 rounded-2xl border border-gray-700/60 bg-black/75 p-4 shadow-lg"
            >
                <div class="mb-2 flex items-center justify-between text-sm font-semibold text-gray-100">
                    <span>Создание графа</span>
                    <span>{{ graphRenderProgress }}%</span>
                </div>
            </div>
            <div id="vlan-network" :class="['min-h-120 h-full w-full', vlanMaximized ? 'maximized' : '']" />
        </div>

        <div
            v-show="mode === 'mac'"
            :class="['relative h-150 min-h-120 sm:h-225', macMaximized ? 'maximized-shell' : '']"
        >
            <div v-if="macRendered" class="absolute! top-6 right-30 left-3 z-101 flex items-center gap-2 sm:left-auto">
                <InputText
                    :model-value="graphNodeSearch"
                    placeholder="Node"
                    class="w-full rounded-xl! bg-white/95! text-gray-900! dark:bg-gray-950/80! dark:text-gray-100! border-gray-200/80! dark:border-gray-700/60! sm:w-44!"
                    @update:model-value="$emit('update:graphNodeSearch', String($event ?? ''))"
                    @keyup.enter="$emit('focus-node')"
                />
                <Button
                    icon="pi pi-search"
                    rounded
                    severity="secondary"
                    v-tooltip.bottom="'Найти узел'"
                    @click="$emit('focus-node')"
                />
                <span
                    v-if="graphSearchMatchesCount > 0"
                    class="rounded-lg bg-black/60 px-2 py-1 font-mono text-xs text-white"
                >
                    {{ graphSearchMatchIndex }}/{{ graphSearchMatchesCount }}
                </span>
            </div>
            <Button
                v-if="macRendered"
                class="absolute! z-101 top-6 right-18 rounded-xl!"
                icon="pi pi-sliders-h"
                rounded
                severity="secondary"
                v-tooltip.bottom="physicsMenuVisible ? 'Скрыть настройки физики' : 'Показать настройки физики'"
                @click="$emit('toggle-physics')"
            />
            <Button
                v-if="macRendered"
                class="absolute! z-101 top-6 right-6 rounded-xl!"
                :icon="macMaximized ? 'pi pi-times' : 'pi pi-expand'"
                rounded
                severity="secondary"
                v-tooltip.bottom="macMaximized ? 'Выйти из полного экрана' : 'На весь экран'"
                @click="$emit('toggle-maximize-mac')"
            />
            <div
                v-if="graphRenderLoading && mode === 'mac'"
                class="absolute! z-102 left-3 right-3 top-16 rounded-2xl border border-gray-700/60 bg-black/75 p-4 shadow-lg"
            >
                <div class="mb-2 flex items-center justify-between text-sm font-semibold text-gray-100">
                    <span>Создание графа</span>
                    <span>{{ graphRenderProgress }}%</span>
                </div>
            </div>
            <div id="mac-network" :class="['min-h-120 h-full w-full', macMaximized ? 'maximized' : '']" />
        </div>
    </section>
</template>

<script setup lang="ts">
import type { TracerouteMode } from "./types";

defineProps<{
    mode: TracerouteMode;
    vlanRendered: boolean;
    macRendered: boolean;
    vlanMaximized: boolean;
    macMaximized: boolean;
    maximized: boolean;
    graphNodeSearch: string;
    graphSearchMatchesCount: number;
    graphSearchMatchIndex: number;
    graphRenderLoading: boolean;
    graphRenderProgress: number;
    physicsMenuVisible: boolean;
}>();

defineEmits<{
    "update:graphNodeSearch": [value: string];
    "focus-node": [];
    "toggle-physics": [];
    "toggle-maximize-vlan": [];
    "toggle-maximize-mac": [];
}>();
</script>

<style scoped>
.maximized-shell {
    position: fixed !important;
    inset: 0 !important;
    z-index: 10000 !important;
    width: 100vw !important;
    height: 100vh !important;
    margin: 0 !important;
    padding: 0 !important;
    background-color: #000000 !important;
    border-radius: 0 !important;
}

.maximized {
    width: 100vw !important;
    height: 100vh !important;
    max-width: 100vw !important;
    max-height: 100vh !important;
    margin: 0 !important;
    background-color: #000000 !important;
    border-radius: 0 !important;
}

.maximized :deep(.vis-network),
.maximized :deep(.vis-network > canvas) {
    width: 100% !important;
    height: 100% !important;
}
</style>
