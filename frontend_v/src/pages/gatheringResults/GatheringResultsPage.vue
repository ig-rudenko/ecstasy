<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import GatheringResultsFilters from "@/pages/gatheringResults/components/GatheringResultsFilters.vue";
import GatheringTimeline from "@/pages/gatheringResults/components/GatheringTimeline.vue";
import { getGatheringResultLookups, getGatheringResults, getGatheringTimeline } from "@/services/gatheringResults";
import type {
    DeviceGatheringResult,
    GatheringResultFilters,
    GatheringResultLookups,
    GatheringResultStatus,
    GatheringTaskStatus,
} from "@/types/gatheringResults";
import permissions from "@/services/permissions.ts";
import { useRouter } from "vue-router";

const pageSize = 50;
const lookups = ref<GatheringResultLookups>({
    device_groups: [],
    vendors: [],
    models: [],
    task_names: [],
    error_types: [],
});
const filters = ref<GatheringResultFilters>(createDefaultFilters());
const rows = ref<DeviceGatheringResult[]>([]);
const timelineRows = ref<DeviceGatheringResult[]>([]);
const total = ref(0);
const page = ref(1);
const timelineTaskName = ref<string | null>(null);
const loading = ref(false);
const timelineLoading = ref(false);
const timelineTruncated = ref(false);
const errorMessage = ref("");
const selectedResult = ref<DeviceGatheringResult | null>(null);
const detailsVisible = ref(false);

const failedCount = computed(() => rows.value.filter((result) => result.status === "FAILURE").length);
const runningCount = computed(() => rows.value.filter((result) => result.status === "RUNNING").length);

function createDefaultFilters(): GatheringResultFilters {
    const resultStartedAfter = new Date();
    resultStartedAfter.setDate(resultStartedAfter.getDate() - 1);
    return {
        deviceGroup: null,
        deviceName: "",
        vendor: null,
        model: null,
        taskStatus: null,
        taskName: null,
        taskStartedAfter: null,
        taskStartedBefore: null,
        resultStatus: null,
        resultStartedAfter,
        resultStartedBefore: null,
        errorType: null,
        errorMessage: "",
    };
}

async function loadLookups(): Promise<void> {
    lookups.value = await getGatheringResultLookups();
}

async function loadTable(targetPage = 1): Promise<void> {
    loading.value = true;
    try {
        const response = await getGatheringResults(filters.value, targetPage, pageSize);
        rows.value = response.results;
        total.value = response.count;
        page.value = targetPage;
    } finally {
        loading.value = false;
    }
}

async function loadTimeline(): Promise<void> {
    timelineLoading.value = true;
    try {
        const response = await getGatheringTimeline(filters.value, timelineTaskName.value);
        timelineRows.value = response.results;
        timelineTruncated.value = response.truncated;
    } finally {
        timelineLoading.value = false;
    }
}

async function refresh(): Promise<void> {
    errorMessage.value = "";
    try {
        await Promise.all([loadTable(1), loadTimeline(), loadLookups()]);
    } catch {
        errorMessage.value = "Не удалось загрузить результаты периодического сбора.";
    }
}

async function resetFilters(): Promise<void> {
    filters.value = createDefaultFilters();
    timelineTaskName.value = null;
    await refresh();
}

async function changeTimelineTaskName(value: string | null): Promise<void> {
    timelineTaskName.value = value;
    errorMessage.value = "";
    try {
        await loadTimeline();
    } catch {
        errorMessage.value = "Не удалось обновить временную шкалу.";
    }
}

async function changePage(targetPage: number): Promise<void> {
    errorMessage.value = "";
    try {
        await loadTable(targetPage);
    } catch {
        errorMessage.value = "Не удалось загрузить страницу результатов.";
    }
}

function showDetails(result: DeviceGatheringResult): void {
    selectedResult.value = result;
    detailsVisible.value = true;
}

function formatDate(value: string | null): string {
    return value ? new Date(value).toLocaleString("ru-RU") : "—";
}

function duration(result: DeviceGatheringResult): string {
    const end = result.finished_at ? new Date(result.finished_at).getTime() : Date.now();
    const milliseconds = Math.max(0, end - new Date(result.started_at).getTime());
    if (milliseconds < 1000) return `${milliseconds} мс`;
    if (milliseconds < 60000) return `${(milliseconds / 1000).toFixed(1)} с`;
    return `${(milliseconds / 60000).toFixed(1)} мин`;
}

function resultStatusLabel(status: GatheringResultStatus): string {
    return {
        RUNNING: "Выполняется",
        SUCCESS: "Успешно",
        SKIPPED: "Пропущено",
        FAILURE: "Ошибка",
    }[status];
}

function taskStatusLabel(status: GatheringTaskStatus): string {
    return {
        RUNNING: "Выполняется",
        SUCCESS: "Успешно",
        PARTIAL: "Частично",
        FAILURE: "Ошибка",
    }[status];
}

function statusSeverity(status: GatheringResultStatus | GatheringTaskStatus) {
    if (status === "SUCCESS") return "success";
    if (status === "FAILURE") return "danger";
    if (status === "RUNNING") return "info";
    if (status === "PARTIAL") return "warn";
    return "secondary";
}

onMounted(async () => {
    if (!permissions.hasGatheringResultAccessPermission()) await useRouter().push("/");
    await refresh();
});
</script>

<template>
    <main class="mx-auto sm:px-6 sm:py-8 lg:px-8">
        <div class="flex flex-col gap-6">
            <section
                class="relative overflow-hidden border-gray-200/70 bg-white/70 backdrop-blur sm:rounded-4xl sm:border sm:p-7 dark:border-gray-700/70 dark:bg-gray-900/40"
            >
                <div
                    class="pointer-events-none absolute inset-0 bg-linear-to-br from-indigo-500/10 via-transparent to-emerald-500/10"
                />
                <div class="relative flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
                    <div class="flex items-center gap-4">
                        <div
                            class="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-700 ring-1 ring-indigo-100 dark:bg-indigo-950/40 dark:text-indigo-200 dark:ring-indigo-900/60"
                        >
                            <i class="pi pi-chart-bar text-xl" />
                        </div>
                        <div>
                            <h1 class="text-2xl font-semibold text-gray-900 sm:text-3xl dark:text-gray-100">
                                Периодический сбор
                            </h1>
                            <p class="mt-1 text-xs text-gray-500 sm:text-sm dark:text-gray-400">
                                Время выполнения и результаты опросов по каждому оборудованию
                            </p>
                        </div>
                    </div>

                    <div class="grid grid-cols-3 gap-3 xl:min-w-128">
                        <div
                            class="rounded-2xl border border-gray-200/80 bg-gray-50/80 px-4 py-3 dark:border-gray-700/80 dark:bg-gray-800/60"
                        >
                            <div class="text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">Найдено</div>
                            <div class="mt-1 text-2xl font-semibold text-gray-900 dark:text-gray-100">{{ total }}</div>
                        </div>
                        <div
                            class="rounded-2xl border border-gray-200/80 bg-gray-50/80 px-4 py-3 dark:border-gray-700/80 dark:bg-gray-800/60"
                        >
                            <div class="text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">Активно</div>
                            <div class="mt-1 text-2xl font-semibold text-sky-700 dark:text-sky-300">
                                {{ runningCount }}
                            </div>
                        </div>
                        <div
                            class="rounded-2xl border border-gray-200/80 bg-gray-50/80 px-4 py-3 dark:border-gray-700/80 dark:bg-gray-800/60"
                        >
                            <div class="text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">Ошибки</div>
                            <div class="mt-1 text-2xl font-semibold text-red-700 dark:text-red-300">
                                {{ failedCount }}
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <Message v-if="errorMessage" severity="error" :closable="false">{{ errorMessage }}</Message>

            <Fieldset legend="Фильтры" :toggleable="true" class="bg-white/80! dark:bg-gray-900/45!">
                <GatheringResultsFilters
                    v-model="filters"
                    :lookups="lookups"
                    :loading="loading || timelineLoading"
                    @apply="refresh"
                    @reset="resetFilters"
                />
            </Fieldset>

            <section
                class="border-gray-200/70 bg-white/80 backdrop-blur sm:rounded-4xl sm:border sm:p-6 dark:border-gray-700/70 dark:bg-gray-900/45"
            >
                <GatheringTimeline
                    :results="timelineRows"
                    :taskNames="lookups.task_names"
                    :taskName="timelineTaskName"
                    :loading="timelineLoading"
                    :truncated="timelineTruncated"
                    @update:taskName="changeTimelineTaskName"
                    @select="showDetails"
                />
            </section>

            <section
                class="border-gray-200/70 bg-white/80 backdrop-blur sm:rounded-4xl sm:border sm:p-6 dark:border-gray-700/70 dark:bg-gray-900/45"
            >
                <div class="mb-4">
                    <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Результаты по оборудованию</h2>
                    <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        Отдельная строка для каждого опроса устройства
                    </p>
                </div>
                <DataTable
                    :value="rows"
                    :loading="loading"
                    dataKey="id"
                    stripedRows
                    scrollable
                    scrollHeight="34rem"
                    tableStyle="min-width: 76rem"
                    @row-click="showDetails($event.data)"
                >
                    <Column header="Оборудование" frozen style="min-width: 13rem">
                        <template #body="{ data }">
                            <button class="text-left" type="button" @click.stop="showDetails(data)">
                                <span class="block font-semibold text-indigo-700 dark:text-indigo-300">
                                    {{ data.device.name }}
                                </span>
                                <span class="text-xs text-gray-500 dark:text-gray-400">{{ data.device.ip }}</span>
                            </button>
                        </template>
                    </Column>
                    <Column field="device.group.name" header="Группа" style="min-width: 10rem" />
                    <Column header="Вендор / модель" style="min-width: 12rem">
                        <template #body="{ data }">
                            {{ [data.device.vendor, data.device.model].filter(Boolean).join(" · ") || "—" }}
                        </template>
                    </Column>
                    <Column field="task.name" header="Задача" style="min-width: 12rem" />
                    <Column header="Статус" style="min-width: 9rem">
                        <template #body="{ data }">
                            <Tag :value="resultStatusLabel(data.status)" :severity="statusSeverity(data.status)" />
                        </template>
                    </Column>
                    <Column header="Начало" style="min-width: 11rem">
                        <template #body="{ data }">{{ formatDate(data.started_at) }}</template>
                    </Column>
                    <Column header="Длительность" style="min-width: 8rem">
                        <template #body="{ data }">{{ duration(data) }}</template>
                    </Column>
                    <Column header="Ошибка" style="min-width: 16rem">
                        <template #body="{ data }">
                            <div v-if="data.error_type || data.error_message" class="max-w-72">
                                <div class="font-medium text-red-700 dark:text-red-300">
                                    {{ data.error_type || "Ошибка" }}
                                </div>
                                <div class="truncate text-xs text-gray-500 dark:text-gray-400">
                                    {{ data.error_message }}
                                </div>
                            </div>
                            <span v-else>—</span>
                        </template>
                    </Column>
                </DataTable>
                <Paginator
                    v-if="total > pageSize"
                    :rows="pageSize"
                    :totalRecords="total"
                    :first="(page - 1) * pageSize"
                    class="mt-4"
                    @page="changePage($event.page + 1)"
                />
            </section>
        </div>
    </main>

    <Dialog v-model:visible="detailsVisible" modal header="Результат опроса" class="w-[min(42rem,95vw)]">
        <div v-if="selectedResult" class="space-y-5">
            <div class="flex flex-wrap items-start justify-between gap-3">
                <div>
                    <div class="text-xl font-semibold text-gray-900 dark:text-gray-100">
                        {{ selectedResult.device.name }}
                    </div>
                    <div class="text-sm text-gray-500 dark:text-gray-400">
                        {{ selectedResult.device.ip }} · {{ selectedResult.device.group.name }}
                    </div>
                </div>
                <Tag
                    :value="resultStatusLabel(selectedResult.status)"
                    :severity="statusSeverity(selectedResult.status)"
                />
            </div>

            <div class="grid gap-3 sm:grid-cols-2">
                <div class="rounded-2xl bg-gray-50 p-4 dark:bg-gray-800/70">
                    <div class="text-xs uppercase text-gray-500">Задача</div>
                    <div class="mt-1 font-medium">{{ selectedResult.task.name }}</div>
                    <div class="mt-2 flex items-center gap-2 text-sm">
                        <Tag
                            :value="taskStatusLabel(selectedResult.task.status)"
                            :severity="statusSeverity(selectedResult.task.status)"
                        />
                        <span>{{ selectedResult.task.total_devices }} устройств</span>
                    </div>
                </div>
                <div class="rounded-2xl bg-gray-50 p-4 dark:bg-gray-800/70">
                    <div class="text-xs uppercase text-gray-500">Оборудование</div>
                    <div class="mt-1 font-medium">
                        {{
                            [selectedResult.device.vendor, selectedResult.device.model].filter(Boolean).join(" · ") ||
                            "—"
                        }}
                    </div>
                    <div class="mt-2 text-sm text-gray-500">{{ selectedResult.device.group.name }}</div>
                </div>
            </div>

            <dl class="grid gap-x-5 gap-y-3 text-sm sm:grid-cols-[10rem_1fr]">
                <dt class="text-gray-500">Начало опроса</dt>
                <dd>{{ formatDate(selectedResult.started_at) }}</dd>
                <dt class="text-gray-500">Завершение</dt>
                <dd>{{ formatDate(selectedResult.finished_at) }}</dd>
                <dt class="text-gray-500">Длительность</dt>
                <dd>{{ duration(selectedResult) }}</dd>
                <dt class="text-gray-500">Celery task ID</dt>
                <dd class="break-all font-mono text-xs">{{ selectedResult.task.task_id }}</dd>
            </dl>

            <Message
                v-if="selectedResult.error_type || selectedResult.error_message"
                severity="error"
                :closable="false"
            >
                <div class="font-semibold">{{ selectedResult.error_type || "Ошибка" }}</div>
                <div class="mt-1 whitespace-pre-wrap break-words text-sm">{{ selectedResult.error_message }}</div>
            </Message>
        </div>
    </Dialog>
</template>
