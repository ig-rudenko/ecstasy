<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";
import { Timeline } from "vis-timeline/peer";
import type { DataGroup, DataItem, TimelineOptions } from "vis-timeline";
import "vis-timeline/styles/vis-timeline-graph2d.css";

import type { DeviceGatheringResult } from "@/types/gatheringResults";

const props = defineProps<{
    results: DeviceGatheringResult[];
    taskNames: string[];
    taskName: string | null;
    loading: boolean;
    truncated: boolean;
}>();

const emit = defineEmits<{
    "update:taskName": [value: string | null];
    select: [result: DeviceGatheringResult];
}>();

const container = ref<HTMLElement | null>(null);
let timeline: Timeline | null = null;

const taskNameOptions = computed(() => [
    { label: "Все задачи", value: null },
    ...props.taskNames.map((name) => ({ label: name, value: name })),
]);

function textElement(value: string): HTMLSpanElement {
    const element = document.createElement("span");
    element.textContent = value;
    return element;
}

function escapeHtml(value: string): string {
    const element = document.createElement("div");
    element.textContent = value;
    return element.innerHTML;
}

function renderTimeline(): void {
    timeline?.destroy();
    timeline = null;
    if (!container.value || props.results.length === 0) return;

    const devices = new Map<number, DeviceGatheringResult["device"]>();
    props.results.forEach((result) => devices.set(result.device.id, result.device));

    const groups: DataGroup[] = [...devices.values()]
        .sort((left, right) => left.name.localeCompare(right.name))
        .map((device) => ({
            id: device.id,
            content: textElement(device.name),
            title: `${device.name} · ${device.ip}`,
        }));
    const items: DataItem[] = props.results.map((result) => ({
        id: result.id,
        group: result.device.id,
        start: new Date(result.started_at),
        end: result.finished_at ? new Date(result.finished_at) : new Date(),
        content: escapeHtml(result.task.name),
        className: `gathering-result gathering-result-${result.status.toLowerCase()}`,
        type: "range",
    }));
    const options: TimelineOptions = {
        height: "460px",
        stack: true,
        selectable: true,
        showCurrentTime: true,
        horizontalScroll: true,
        zoomKey: "ctrlKey",
        orientation: { axis: "top", item: "top" },
        margin: { axis: 12, item: { horizontal: 4, vertical: 6 } },
        tooltip: { followMouse: true },
    };

    timeline = new Timeline(container.value, items, groups, options);
    timeline.on("select", ({ items: selectedItems }: { items: Array<number | string> }) => {
        const selectedId = Number(selectedItems[0]);
        const result = props.results.find((item) => item.id === selectedId);
        if (result) emit("select", result);
    });
    timeline.fit({ animation: false });
}

watch(
    () => props.results,
    async () => {
        await nextTick();
        renderTimeline();
    },
    { immediate: true }
);

onBeforeUnmount(() => timeline?.destroy());
</script>

<template>
    <div>
        <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
                <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Временная шкала опросов</h2>
                <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    Строки — оборудование, ширина блока — длительность опроса. Масштабирование: Ctrl + колесо.
                </p>
            </div>
            <Select
                :modelValue="taskName"
                :options="taskNameOptions"
                optionLabel="label"
                optionValue="value"
                class="w-full md:w-72"
                aria-label="Имя периодической задачи"
                @update:modelValue="emit('update:taskName', $event)"
            />
        </div>

        <Message v-if="truncated" severity="warn" :closable="false" class="mb-3">
            На графике показаны первые 5000 результатов. Сузьте временной диапазон или фильтры.
        </Message>

        <div class="relative min-h-80">
            <div
                v-if="loading"
                class="absolute inset-0 z-10 flex items-center justify-center rounded-2xl bg-white/70 backdrop-blur-sm dark:bg-gray-900/70"
            >
                <ProgressSpinner class="h-10! w-10!" />
            </div>
            <div
                v-if="!loading && results.length === 0"
                class="flex min-h-80 flex-col items-center justify-center rounded-2xl border border-dashed border-gray-300 text-gray-500 dark:border-gray-700 dark:text-gray-400"
            >
                <i class="pi pi-chart-bar mb-3 text-3xl" />
                Нет опросов для выбранных фильтров
            </div>
            <div v-show="results.length > 0" ref="container" class="gathering-timeline overflow-hidden rounded-2xl" />
        </div>
    </div>
</template>

<style scoped>
:deep(.vis-timeline) {
    border-color: rgb(209 213 219 / 0.8);
    border-radius: 1rem;
    font-family: inherit;
}

:deep(.vis-labelset .vis-label),
:deep(.vis-time-axis .vis-text) {
    color: rgb(55 65 81);
}

:deep(.vis-item.gathering-result) {
    border-width: 1px;
    border-radius: 0.5rem;
    color: rgb(17 24 39);
    font-size: 0.75rem;
    font-weight: 600;
}

:deep(.vis-item.gathering-result-success) {
    border-color: rgb(16 185 129);
    background: rgb(167 243 208);
}

:deep(.vis-item.gathering-result-running) {
    border-color: rgb(59 130 246);
    background: rgb(191 219 254);
}

:deep(.vis-item.gathering-result-skipped) {
    border-color: rgb(107 114 128);
    background: rgb(229 231 235);
}

:deep(.vis-item.gathering-result-failure) {
    border-color: rgb(239 68 68);
    background: rgb(254 202 202);
}

:global(.dark) :deep(.vis-timeline),
:global(.dark) :deep(.vis-panel),
:global(.dark) :deep(.vis-labelset .vis-label) {
    border-color: rgb(55 65 81 / 0.8);
    background: rgb(17 24 39);
}

:global(.dark) :deep(.vis-labelset .vis-label),
:global(.dark) :deep(.vis-time-axis .vis-text) {
    color: rgb(209 213 219);
}

:global(.dark) :deep(.vis-grid.vis-minor) {
    border-color: rgb(55 65 81 / 0.55);
}
</style>
