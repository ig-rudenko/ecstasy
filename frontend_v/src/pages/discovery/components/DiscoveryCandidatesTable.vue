<script setup lang="ts">
import { computed, reactive } from "vue";
import MultiSelect from "primevue/multiselect";
import type { DataTableSortEvent } from "primevue/datatable";

import { verboseDatetime } from "@/formats";
import { DiscoveryCandidate, DiscoveryCandidateTableQuery } from "@/services/discovery";

type AuthCheckStatusFilter = "" | DiscoveryCandidate["authCheckStatus"];

type TextFilterKey = "name" | "ip" | "model" | "osVersion" | "lastError" | "authCheckError";

interface TextFilterField {
    key: TextFilterKey;
    label: string;
    placeholder: string;
    wide?: boolean;
}

const primaryTextFilterFields: TextFilterField[] = [
    { key: "name", label: "Имя", placeholder: "" },
    { key: "ip", label: "IP-адрес", placeholder: "" },
    { key: "model", label: "Модель", placeholder: "" },
    { key: "osVersion", label: "Версия ОС", placeholder: "" },
];

const errorTextFilterFields: TextFilterField[] = [
    { key: "lastError", label: "Последняя ошибка", placeholder: "" },
    {
        key: "authCheckError",
        label: "Ошибка проверки AuthGroup",
        placeholder: "",
        wide: true,
    },
];

const props = defineProps<{
    candidates: DiscoveryCandidate[];
    totalRecords: number;
    query: DiscoveryCandidateTableQuery;
    loading: boolean;
    deletingCandidateId: number | null;
    rescanningCandidateId: number | null;
    rescanningSelected: boolean;
    selectedIds: number[];
}>();

const emit = defineEmits<{
    (e: "update:selectedIds", value: number[]): void;
    (e: "query-change", value: DiscoveryCandidateTableQuery): void;
    (e: "accept", candidate: DiscoveryCandidate): void;
    (e: "quick-accept", candidate: DiscoveryCandidate): void;
    (e: "ignore", candidate: DiscoveryCandidate): void;
    (e: "delete", event: MouseEvent, candidate: DiscoveryCandidate): void;
    (e: "rescan", event: MouseEvent, candidate: DiscoveryCandidate): void;
    (e: "delete-selected", event: MouseEvent): void;
    (e: "rescan-selected", event: MouseEvent): void;
    (e: "quick-accept-selected", event: MouseEvent): void;
}>();

const filters = reactive<DiscoveryCandidateTableQuery>({
    ...props.query,
    protocols: [...props.query.protocols],
});

const authCheckStatusOptions: { label: string; value: AuthCheckStatusFilter }[] = [
    { label: "Все статусы", value: "" },
    { label: "Проверка успешна", value: "SUCCESS" },
    { label: "Проверка не пройдена", value: "FAILED" },
    { label: "Не проверялась", value: "UNKNOWN" },
];

const protocolOptions = ["ping", "snmp", "ssh", "telnet"];
const pageCandidateIds = computed<number[]>(() => props.candidates.map((candidate) => candidate.id));
const sortField = computed<string | undefined>(() => filters.ordering.replace(/^-/, "") || undefined);
const sortOrder = computed<1 | -1 | undefined>(() => {
    if (!filters.ordering) {
        return undefined;
    }
    return filters.ordering.startsWith("-") ? -1 : 1;
});

const allFilteredSelected = computed<boolean>(
    () =>
        pageCandidateIds.value.length > 0 &&
        pageCandidateIds.value.every((candidateId) => props.selectedIds.includes(candidateId))
);

const someFilteredSelected = computed<boolean>(
    () =>
        !allFilteredSelected.value &&
        pageCandidateIds.value.some((candidateId) => props.selectedIds.includes(candidateId))
);

const hasActiveFilters = computed<boolean>(() =>
    Object.entries(filters).some(
        ([key, value]) =>
            key !== "ordering" && (Array.isArray(value) ? value.length > 0 : value !== "" && value != null)
    )
);

function getEnabledProtocols(candidate: DiscoveryCandidate): string[] {
    return Object.entries(candidate.detectedProtocols)
        .filter(([, enabled]) => enabled)
        .map(([protocol]) => protocol);
}

function toggleAllFiltered(value: boolean): void {
    const filteredIds = new Set(pageCandidateIds.value);
    if (value) {
        emit("update:selectedIds", [...new Set([...props.selectedIds, ...filteredIds])]);
        return;
    }
    emit(
        "update:selectedIds",
        props.selectedIds.filter((candidateId) => !filteredIds.has(candidateId))
    );
}

function toggleOne(candidateId: number, checked: boolean): void {
    if (checked) {
        if (!props.selectedIds.includes(candidateId)) {
            emit("update:selectedIds", [...props.selectedIds, candidateId]);
        }
        return;
    }
    emit(
        "update:selectedIds",
        props.selectedIds.filter((id) => id !== candidateId)
    );
}

function isSelected(candidateId: number): boolean {
    return props.selectedIds.includes(candidateId);
}

function clearFilters(): void {
    Object.assign(filters, {
        name: "",
        ip: "",
        authCheckStatus: "",
        confidenceMin: null,
        confidenceMax: null,
        protocols: [],
        model: "",
        osVersion: "",
        lastError: "",
        authCheckError: "",
        ordering: "",
    });
    emitQueryChange();
}

function applyFilters(): void {
    emitQueryChange();
}

function handleSort(event: DataTableSortEvent): void {
    if (typeof event.sortField !== "string" || !event.sortOrder) {
        filters.ordering = "";
    } else {
        filters.ordering = `${event.sortOrder === -1 ? "-" : ""}${event.sortField}`;
    }
    emitQueryChange();
}

function emitQueryChange(): void {
    emit("query-change", {
        ...filters,
        protocols: [...filters.protocols],
    });
}

function statusClass(status: string): string {
    if (["CREATED"].includes(status)) {
        return "bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200";
    }
    if (["READY", "SUCCESS"].includes(status)) {
        return "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200";
    }
    if (["FAILED", "FAILURE"].includes(status)) {
        return "bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200";
    }
    if (["DUPLICATE", "IGNORED", "REVOKED"].includes(status)) {
        return "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200";
    }
    return "bg-slate-100 text-slate-700 dark:bg-slate-800/70 dark:text-slate-200";
}

function authCheckClass(status: DiscoveryCandidate["authCheckStatus"]): string {
    if (status === "SUCCESS") {
        return "bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-200 dark:ring-emerald-800";
    }
    if (status === "FAILED") {
        return "bg-rose-50 text-rose-700 ring-rose-200 dark:bg-rose-900/20 dark:text-rose-200 dark:ring-rose-800";
    }
    return "bg-slate-50 text-slate-600 ring-slate-200 dark:bg-slate-800/50 dark:text-slate-300 dark:ring-slate-700";
}

function authCheckLabel(status: DiscoveryCandidate["authCheckStatus"]): string {
    if (status === "SUCCESS") {
        return "AuthGroup проверена";
    }
    if (status === "FAILED") {
        return "AuthGroup не подошла";
    }
    return "Не проверялась";
}
</script>

<template>
    <div
        class="overflow-hidden rounded-[1.75rem] border border-gray-200/70 bg-white/70 backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/40"
    >
        <div class="border-b border-gray-200/70 p-3 dark:border-gray-700/70">
            <div class="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
                <div class="flex flex-wrap items-center gap-2">
                    <Button
                        icon="pi pi-plus-circle"
                        label="Быстро добавить выбранные"
                        size="small"
                        class="rounded-2xl!"
                        :disabled="!selectedIds.length || loading"
                        @click="(event: MouseEvent) => emit('quick-accept-selected', event)"
                    />
                    <Button
                        icon="pi pi-refresh"
                        label="Переопросить выбранные"
                        size="small"
                        severity="secondary"
                        outlined
                        class="rounded-2xl!"
                        :disabled="!selectedIds.length || loading || rescanningSelected"
                        :loading="rescanningSelected"
                        @click="(event: MouseEvent) => emit('rescan-selected', event)"
                    />
                    <Button
                        icon="pi pi-trash"
                        label="Удалить выбранные"
                        size="small"
                        severity="danger"
                        outlined
                        class="rounded-2xl!"
                        :disabled="!selectedIds.length || loading"
                        @click="(event: MouseEvent) => emit('delete-selected', event)"
                    />
                </div>
                <div class="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                    <span>На странице: {{ candidates.length }}</span>
                    <span>Найдено: {{ totalRecords }}</span>
                    <span>Выбрано: {{ selectedIds.length }}</span>
                </div>
            </div>
        </div>

        <div class="border-b border-gray-200/70 bg-gray-50/60 p-3 dark:border-gray-700/70 dark:bg-gray-950/20">
            <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
                <div>
                    <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">Фильтры кандидатов</div>
                    <div class="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
                        Фильтрация и сортировка выполняются на сервере до пагинации.
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <Button
                        icon="pi pi-filter"
                        label="Применить"
                        size="small"
                        class="rounded-xl!"
                        :loading="loading"
                        @click="applyFilters"
                    />
                    <Button
                        icon="pi pi-filter-slash"
                        label="Сбросить"
                        size="small"
                        severity="secondary"
                        text
                        class="rounded-xl!"
                        :disabled="!hasActiveFilters && !filters.ordering"
                        @click="clearFilters"
                    />
                </div>
            </div>

            <div class="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
                <label
                    v-for="filterField in primaryTextFilterFields"
                    :key="filterField.key"
                    class="flex flex-col gap-1.5 text-xs font-medium text-gray-600 dark:text-gray-300"
                >
                    {{ filterField.label }}
                    <InputText
                        v-model="filters[filterField.key]"
                        size="small"
                        :placeholder="filterField.placeholder"
                        fluid
                        @keyup.enter="applyFilters"
                        class="rounded-xl"
                    />
                </label>
                <label class="flex flex-col gap-1.5 text-xs font-medium text-gray-600 dark:text-gray-300">
                    Проверка AuthGroup
                    <Select
                        v-model="filters.authCheckStatus"
                        :options="authCheckStatusOptions"
                        optionLabel="label"
                        optionValue="value"
                        size="small"
                        fluid
                        class="rounded-xl"
                    />
                </label>
                <div class="flex flex-col gap-1.5 text-xs font-medium text-gray-600 dark:text-gray-300">
                    Confidence
                    <div class="grid grid-cols-2 gap-2">
                        <InputNumber
                            v-model="filters.confidenceMin"
                            :min="0"
                            :max="100"
                            size="small"
                            placeholder="От"
                            fluid
                            input-class="rounded-xl"
                        />
                        <InputNumber
                            v-model="filters.confidenceMax"
                            :min="0"
                            :max="100"
                            size="small"
                            placeholder="До"
                            fluid
                            input-class="rounded-xl"
                        />
                    </div>
                </div>
                <label class="flex flex-col gap-1.5 text-xs font-medium text-gray-600 dark:text-gray-300">
                    Требуемые протоколы
                    <MultiSelect
                        v-model="filters.protocols"
                        :options="protocolOptions"
                        :maxSelectedLabels="2"
                        selectedItemsLabel="Выбрано: {0}"
                        placeholder="Любые протоколы"
                        size="small"
                        filter
                        fluid
                        class="rounded-xl"
                    >
                        <template #option="{ option }">{{ option.toUpperCase() }}</template>
                    </MultiSelect>
                </label>
                <label
                    v-for="filterField in errorTextFilterFields"
                    :key="filterField.key"
                    class="flex flex-col gap-1.5 text-xs font-medium text-gray-600 dark:text-gray-300"
                    :class="{ 'md:col-span-2 xl:col-span-4': filterField.wide }"
                >
                    {{ filterField.label }}
                    <InputText
                        v-model="filters[filterField.key]"
                        size="small"
                        :placeholder="filterField.placeholder"
                        fluid
                        @keyup.enter="applyFilters"
                        class="rounded-xl"
                    />
                </label>
            </div>
        </div>

        <DataTable
            :value="candidates"
            dataKey="id"
            :loading="loading"
            lazy
            scrollable
            removable-sort
            striped-rows
            :sortField="sortField"
            :sortOrder="sortOrder"
            class="text-sm"
            :tableStyle="{ minWidth: '120rem' }"
            @sort="handleSort"
            :pt="{
                header: { class: 'hidden!' },
                column: {
                    headerCell: {
                        class: 'bg-gray-50/90 dark:bg-gray-900/90 border-b border-gray-200/80 dark:border-gray-700/80 text-xs uppercase tracking-wide text-gray-600 dark:text-gray-300',
                    },
                    bodyCell: {
                        class: 'align-top border-b border-gray-200/60 dark:border-gray-700/60',
                    },
                },
            }"
        >
            <template #empty>
                <div class="px-4 py-10 text-center text-sm text-gray-500">По текущим фильтрам кандидаты не найдены</div>
            </template>

            <Column headerStyle="width: 3rem" bodyStyle="width: 3rem">
                <template #header>
                    <Checkbox
                        :binary="true"
                        :modelValue="allFilteredSelected"
                        :indeterminate="someFilteredSelected"
                        aria-label="Выбрать всех отфильтрованных кандидатов"
                        @update:modelValue="toggleAllFiltered"
                    />
                </template>
                <template #body="{ data }: { data: DiscoveryCandidate }">
                    <Checkbox
                        :binary="true"
                        :modelValue="isSelected(data.id)"
                        :aria-label="`Выбрать кандидата ${data.name || data.ip}`"
                        @update:modelValue="(value: boolean) => toggleOne(data.id, value)"
                    />
                </template>
            </Column>

            <Column field="name" header="Кандидат" :sortable="true">
                <template #body="{ data }: { data: DiscoveryCandidate }">
                    <div class="min-w-48">
                        <div class="font-semibold text-gray-900 dark:text-gray-100">{{ data.name || "Без имени" }}</div>
                        <div class="mt-1 font-mono text-xs text-gray-500">{{ data.ip }}</div>
                    </div>
                </template>
            </Column>

            <Column field="model" header="Устройство" :sortable="true">
                <template #body="{ data }: { data: DiscoveryCandidate }">
                    <div class="min-w-56">
                        <div class="text-sm font-medium text-gray-800 dark:text-gray-200">
                            {{ [data.vendor, data.model].filter(Boolean).join(" · ") || "Не определено" }}
                        </div>
                        <div class="mt-1 text-xs text-gray-500">ОС: {{ data.osVersion || "—" }}</div>
                        <div class="mt-1 text-xs text-gray-500">
                            {{ data.serialNumber || data.sysName || data.sysDescr || "Без fingerprint" }}
                        </div>
                    </div>
                </template>
            </Column>

            <Column field="status" header="Discovery" :sortable="true">
                <template #body="{ data }: { data: DiscoveryCandidate }">
                    <div class="min-w-28">
                        <span
                            class="inline-flex rounded-full px-2 py-1 text-xs font-semibold"
                            :class="statusClass(data.status)"
                        >
                            {{ data.status }}
                        </span>
                    </div>
                </template>
            </Column>

            <Column field="confidence" header="Confidence" :sortable="true">
                <template #body="{ data }: { data: DiscoveryCandidate }">
                    <span class="font-mono font-semibold text-gray-800 dark:text-gray-100">{{ data.confidence }}</span>
                </template>
            </Column>

            <Column header="Протоколы">
                <template #body="{ data }: { data: DiscoveryCandidate }">
                    <div class="flex min-w-36 flex-wrap gap-1">
                        <Tag
                            v-for="protocol in getEnabledProtocols(data)"
                            :key="protocol"
                            severity="success"
                            :value="protocol.toUpperCase()"
                        />
                        <span v-if="!getEnabledProtocols(data).length" class="text-xs text-gray-400"
                            >Не обнаружены</span
                        >
                    </div>
                </template>
            </Column>

            <Column field="authCheckStatus" header="Проверка AuthGroup" :sortable="true">
                <template #body="{ data }: { data: DiscoveryCandidate }">
                    <div class="min-w-96">
                        <span
                            class="inline-flex rounded-full px-3 py-1 text-xs font-semibold ring-1"
                            :class="authCheckClass(data.authCheckStatus)"
                        >
                            {{ authCheckLabel(data.authCheckStatus) }}
                        </span>
                        <pre
                            v-if="data.authCheckError"
                            class="mt-3 max-w-160 whitespace-pre-wrap wrap-break-word rounded-xl border border-rose-200/80 bg-rose-50/70 p-3 font-mono text-xs leading-5 text-rose-800 dark:border-rose-900/70 dark:bg-rose-950/25 dark:text-rose-200"
                            >{{ data.authCheckError }}</pre
                        >
                        <span v-else class="mt-2 block text-xs text-gray-400">Ошибки проверки нет</span>
                    </div>
                </template>
            </Column>

            <Column field="lastSeenAt" header="Последняя активность" :sortable="true">
                <template #body="{ data }: { data: DiscoveryCandidate }">
                    <div class="min-w-80">
                        <div class="text-sm text-gray-700 dark:text-gray-200">
                            {{ verboseDatetime(data.last_seen_at) }}
                        </div>
                        <pre
                            v-if="data.lastError"
                            class="mt-3 max-w-120 whitespace-pre-wrap wrap-break-word rounded-xl border border-amber-200/80 bg-amber-50/70 p-3 font-mono text-xs leading-5 text-amber-900 dark:border-amber-900/70 dark:bg-amber-950/25 dark:text-amber-100"
                            >{{ data.lastError }}</pre
                        >
                        <span v-else class="mt-2 block text-xs text-gray-400">Последней ошибки нет</span>
                    </div>
                </template>
            </Column>

            <Column header="Действия" headerStyle="width: 15rem" bodyStyle="width: 15rem">
                <template #body="{ data }: { data: DiscoveryCandidate }">
                    <div class="flex flex-wrap w-56 gap-2">
                        <div v-if="data.status === 'READY' || data.status === 'NEW'" class="grid grid-cols-2 gap-2">
                            <Button
                                icon="pi pi-check"
                                label="Принять"
                                size="small"
                                class="rounded-xl!"
                                @click="emit('accept', data)"
                            />
                            <Button
                                icon="pi pi-plus-circle"
                                label="Быстро"
                                size="small"
                                severity="secondary"
                                outlined
                                class="rounded-xl!"
                                @click="emit('quick-accept', data)"
                            />
                        </div>
                        <div class="grid grid-cols-3 gap-2">
                            <Button
                                v-if="data.status !== 'IGNORED' && data.status !== 'CREATED'"
                                v-tooltip.top="'Игнорировать кандидата'"
                                icon="pi pi-eye-slash"
                                size="small"
                                severity="secondary"
                                outlined
                                class="rounded-xl!"
                                :aria-label="`Игнорировать кандидата ${data.name || data.ip}`"
                                @click="emit('ignore', data)"
                            />
                            <span v-else></span>
                            <Button
                                v-tooltip.top="'Переопросить кандидата'"
                                icon="pi pi-refresh"
                                size="small"
                                severity="secondary"
                                outlined
                                class="rounded-xl!"
                                :aria-label="`Переопросить кандидата ${data.name || data.ip}`"
                                :loading="rescanningCandidateId === data.id"
                                @click="(event: MouseEvent) => emit('rescan', event, data)"
                            />
                            <Button
                                v-tooltip.top="'Удалить кандидата'"
                                icon="pi pi-trash"
                                size="small"
                                severity="danger"
                                outlined
                                class="rounded-xl!"
                                :aria-label="`Удалить кандидата ${data.name || data.ip}`"
                                :loading="deletingCandidateId === data.id"
                                @click="(event: MouseEvent) => emit('delete', event, data)"
                            />
                        </div>
                    </div>
                </template>
            </Column>
        </DataTable>
    </div>
</template>
