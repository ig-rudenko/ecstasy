<script lang="ts" setup>
import { onMounted, ref } from "vue";

import errorFmt from "@/errorFmt";
import { verboseDatetime } from "@/formats";
import api from "@/services/api";
import { PaginatedResponse } from "@/types/paginator";

interface MacAddressRow {
    id: number;
    address: string;
    vlan: number;
    type: string;
    device_id: number;
    device_name: string;
    device_ip: string;
    port: string;
    desc: string;
    datetime: string;
}

interface PageEvent {
    page: number;
    rows: number;
}

const props = defineProps<{
    macAddress: string;
}>();

const rows = ref<MacAddressRow[]>([]);
const total = ref(0);
const page = ref(0);
const pageSize = ref(10);
const loading = ref(false);
const error = ref("");
const filters = ref({
    device: "",
    vlan: "",
    port: "",
    desc: "",
});

async function loadRows(targetPage = 0, targetPageSize = pageSize.value) {
    loading.value = true;
    error.value = "";

    try {
        const response = await api.get<PaginatedResponse<MacAddressRow>>("/api/v1/gather/mac-addresses/", {
            params: {
                address: props.macAddress,
                page: targetPage + 1,
                page_size: targetPageSize,
                device: filters.value.device || undefined,
                vlan: filters.value.vlan || undefined,
                port: filters.value.port || undefined,
                desc: filters.value.desc || undefined,
            },
        });
        rows.value = response.data.results;
        total.value = response.data.count;
        page.value = targetPage;
        pageSize.value = targetPageSize;
    } catch (reason) {
        rows.value = [];
        total.value = 0;
        error.value = errorFmt(reason);
    } finally {
        loading.value = false;
    }
}

function applyFilters() {
    loadRows(0);
}

function resetFilters() {
    filters.value = {
        device: "",
        vlan: "",
        port: "",
        desc: "",
    };
    loadRows(0);
}

function onPage(event: PageEvent) {
    loadRows(event.page, event.rows);
}

onMounted(() => loadRows());
</script>

<template>
    <section
        class="rounded-2xl border border-sky-200/80 bg-sky-50/50 p-4 dark:border-sky-900/70 dark:bg-sky-500/10 sm:p-5"
    >
        <div class="flex flex-col gap-4">
            <div>
                <div class="text-xs font-semibold uppercase tracking-[0.18em] text-sky-700 dark:text-sky-200">
                    Собранные MAC-адреса
                </div>
                <div class="mt-1 text-sm text-gray-600 dark:text-gray-300">
                    Данные из последнего сбора таблиц MAC по доступному оборудованию.
                </div>
            </div>

            <form class="grid gap-3 md:grid-cols-2 xl:grid-cols-[1fr_8rem_1fr_1fr_auto]" @submit.prevent="applyFilters">
                <InputText
                    v-model.trim="filters.device"
                    placeholder="Устройство или IP"
                    aria-label="Фильтр по устройству или IP"
                />
                <InputText v-model.trim="filters.vlan" placeholder="VLAN" aria-label="Фильтр по VLAN" />
                <InputText v-model.trim="filters.port" placeholder="Порт" aria-label="Фильтр по порту" />
                <InputText v-model.trim="filters.desc" placeholder="Описание" aria-label="Фильтр по описанию" />
                <div class="flex gap-2">
                    <Button type="submit" icon="pi pi-filter" label="Фильтр" class="grow whitespace-nowrap" />
                    <Button
                        type="button"
                        icon="pi pi-filter-slash"
                        severity="secondary"
                        outlined
                        aria-label="Сбросить фильтры"
                        @click="resetFilters"
                    />
                </div>
            </form>

            <Message v-if="error" severity="error" closable @close="error = ''">
                Не удалось загрузить собранные MAC-адреса: {{ error }}
            </Message>

            <div
                class="overflow-x-auto rounded-2xl border border-gray-200/80 bg-white/80 dark:border-gray-700/80 dark:bg-gray-950/30"
            >
                <DataTable
                    :value="rows"
                    :loading="loading"
                    paginator
                    lazy
                    :rows="pageSize"
                    :first="page * pageSize"
                    :totalRecords="total"
                    :rowsPerPageOptions="[10, 25, 50, 100]"
                    :always-show-paginator="false"
                    paginator-position="both"
                    row-hover
                    class="min-w-208 text-sm"
                    @page="onPage"
                    :pt="{
                        column: {
                            headerCell: {
                                class: 'bg-gray-50/90 dark:bg-gray-900/80 text-xs uppercase tracking-[0.12em] text-gray-500 dark:text-gray-400',
                            },
                        },
                        pcPaginator: {
                            root: {
                                class: 'border-t border-gray-200/80 dark:border-gray-700/80 bg-white/60 dark:bg-gray-900/50',
                            },
                        },
                    }"
                >
                    <template #empty>
                        <div class="py-6 text-center text-sm text-gray-500 dark:text-gray-400">
                            Записи с указанными фильтрами не найдены.
                        </div>
                    </template>

                    <Column field="device_name" header="Устройство">
                        <template #body="{ data }">
                            <router-link
                                :to="{ name: 'device', params: { deviceName: data.device_name } }"
                                class="font-semibold text-sky-700 hover:underline dark:text-sky-300"
                            >
                                {{ data.device_name }}
                            </router-link>
                            <div class="mt-1 font-mono text-xs text-gray-500 dark:text-gray-400">
                                {{ data.device_ip }}
                            </div>
                        </template>
                    </Column>
                    <Column field="vlan" header="VLAN" />
                    <Column field="type" header="Тип" />
                    <Column field="port" header="Порт">
                        <template #body="{ data }">
                            <span class="font-mono">{{ data.port }}</span>
                        </template>
                    </Column>
                    <Column field="desc" header="Описание">
                        <template #body="{ data }">
                            {{ data.desc || "—" }}
                        </template>
                    </Column>
                    <Column field="datetime" header="Собрано">
                        <template #body="{ data }">
                            <span class="whitespace-nowrap">{{ verboseDatetime(data.datetime) }}</span>
                        </template>
                    </Column>
                </DataTable>
            </div>
        </div>
    </section>
</template>
