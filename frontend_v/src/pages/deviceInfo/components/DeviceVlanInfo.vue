<template>
    <Button
        v-if="vlanInfo?.length"
        text
        @click="openDialog"
        v-tooltip.bottom="buttonTooltip"
        :severity="error.status ? 'danger' : 'primary'"
        aria-label="Открыть информацию VLAN"
        class="relative rounded-2xl! border-none! shadow-sm"
    >
        <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" viewBox="0 0 16 16">
            <path
                d="M8.235 1.559a.5.5 0 0 0-.47 0l-7.5 4a.5.5 0 0 0 0 .882L3.188 8 .264 9.559a.5.5 0 0 0 0 .882l7.5 4a.5.5 0 0 0 .47 0l7.5-4a.5.5 0 0 0 0-.882L12.813 8l2.922-1.559a.5.5 0 0 0 0-.882zm3.515 7.008L14.438 10 8 13.433 1.562 10 4.25 8.567l3.515 1.874a.5.5 0 0 0 .47 0zM8 9.433 1.562 6 8 2.567 14.438 6z"
            />
        </svg>
    </Button>

    <Dialog v-model:visible="showDialog" modal maximizable class="w-[min(96vw,1200px)]" content-class="!p-0">
        <template #header>
            <div class="flex min-w-0 items-center gap-3">
                <div
                    class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-sky-50 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="30"
                        height="30"
                        fill="currentColor"
                        viewBox="0 0 16 16"
                    >
                        <path
                            d="M8.235 1.559a.5.5 0 0 0-.47 0l-7.5 4a.5.5 0 0 0 0 .882L3.188 8 .264 9.559a.5.5 0 0 0 0 .882l7.5 4a.5.5 0 0 0 .47 0l7.5-4a.5.5 0 0 0 0-.882L12.813 8l2.922-1.559a.5.5 0 0 0 0-.882zm3.515 7.008L14.438 10 8 13.433 1.562 10 4.25 8.567l3.515 1.874a.5.5 0 0 0 .47 0zM8 9.433 1.562 6 8 2.567 14.438 6z"
                        />
                    </svg>
                </div>
                <div class="min-w-0">
                    <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">VLAN на устройстве</div>
                    <div class="mt-0.5 truncate font-mono text-sm text-gray-500 dark:text-gray-400">
                        {{ deviceName }}
                    </div>
                </div>
            </div>
        </template>

        <div class="flex flex-col gap-4 bg-gray-50/60 p-4 dark:bg-gray-950/30 sm:p-5">
            <Message v-if="error.status" severity="error" class="rounded-2xl!">
                <div class="font-semibold">Ошибка загрузки VLAN</div>
                <div class="mt-1 text-sm">Статус: {{ error.status }}</div>
                <div class="mt-1 text-sm">{{ error.msg }}</div>
            </Message>

            <div
                v-else-if="isLoading"
                class="flex justify-center rounded-3xl border border-dashed border-gray-200/80 bg-white/70 p-10 dark:border-gray-700/80 dark:bg-gray-900/35"
            >
                <ProgressSpinner />
            </div>

            <div
                v-else-if="vlanRows.length"
                class="flex flex-col gap-4 rounded-3xl border border-gray-200/80 bg-white/85 p-4 shadow-sm dark:border-gray-700/80 dark:bg-gray-900/55"
            >
                <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div>
                        <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">Сводка VLAN</div>
                        <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                            Быстрый обзор VLAN, описаний и портов, где они найдены.
                        </div>
                    </div>

                    <IconField class="w-full lg:w-80">
                        <InputIcon class="pi pi-search" />
                        <InputText
                            v-model="vlanFilters.global.value"
                            class="w-full"
                            placeholder="Поиск по VLAN, описанию или порту"
                        />
                    </IconField>
                </div>

                <div class="grid gap-3 sm:grid-cols-3">
                    <article
                        v-for="metric in summaryMetrics"
                        :key="metric.label"
                        class="rounded-2xl border border-gray-200/80 bg-gray-50/80 p-4 dark:border-gray-700/80 dark:bg-gray-800/60"
                    >
                        <div class="text-xs font-semibold uppercase tracking-[0.18em] text-gray-500 dark:text-gray-400">
                            {{ metric.label }}
                        </div>
                        <div class="mt-2 font-mono text-xl font-semibold text-gray-900 dark:text-gray-100">
                            {{ metric.value }}
                        </div>
                        <div v-if="metric.hint" class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                            {{ metric.hint }}
                        </div>
                    </article>
                </div>

                <div
                    class="overflow-hidden rounded-3xl border border-gray-200/80 bg-white/70 dark:border-gray-700/80 dark:bg-gray-950/25"
                >
                    <DataTable
                        :value="vlanRows"
                        v-model:filters="vlanFilters"
                        :globalFilterFields="['vlanText', 'desc', 'portsText']"
                        removable-sort
                        :paginator="vlanRows.length > 12"
                        :rows="12"
                        filterDisplay="row"
                        :always-show-paginator="false"
                        paginator-position="both"
                        row-hover
                        class="text-sm font-mono!"
                        :pt="{
                            header: { class: 'hidden!' },
                            column: {
                                headerCell: {
                                    class: 'bg-gray-50/80 dark:bg-gray-900/80 border-b border-gray-200/80 dark:border-gray-700/80 text-xs uppercase tracking-[0.18em] text-gray-500 dark:text-gray-400',
                                },
                            },
                            pcPaginator: {
                                root: {
                                    class: 'border-t border-gray-200/80 dark:border-gray-700/80 px-2 py-2 bg-white/60 dark:bg-gray-900/50',
                                },
                            },
                        }"
                    >
                        <Column field="vlan" filter-field="vlanText" header="VLAN" :sortable="true">
                            <template #body="{ data }">
                                <div
                                    class="inline-flex items-center gap-2 rounded-full border border-sky-200/80 bg-sky-50 px-3 py-1 font-mono font-semibold text-sky-900 dark:border-sky-900/70 dark:bg-sky-500/15 dark:text-sky-100"
                                >
                                    <span class="inline-flex h-2 w-2 rounded-full bg-sky-500"></span>
                                    {{ data.vlan }}
                                </div>
                            </template>
                            <template #filter="{ filterModel, filterCallback }">
                                <InputText
                                    v-model="filterModel.value"
                                    type="text"
                                    class="min-w-14!"
                                    fluid
                                    @input="filterCallback()"
                                />
                            </template>
                        </Column>

                        <Column field="desc" header="Name" :sortable="true">
                            <template #body="{ data }">
                                <div class="max-w-152 whitespace-normal text-gray-800 dark:text-gray-100">
                                    {{ data.desc || "Без описания" }}
                                </div>
                            </template>
                            <template #filter="{ filterModel, filterCallback }">
                                <InputText
                                    v-model="filterModel.value"
                                    type="text"
                                    class="min-w-20!"
                                    fluid
                                    @input="filterCallback()"
                                />
                            </template>
                        </Column>

                        <Column field="portsText" header="Порты">
                            <template #body="{ data }">
                                <div class="mb-2 flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                                    <i class="pi pi-link" />
                                    <span>{{ data.ports.length }} {{ formatPortsCount(data.ports.length) }}</span>
                                </div>
                                <div class="flex max-h-36 flex-wrap content-start gap-2 overflow-y-auto pr-1">
                                    <div
                                        v-for="port in data.ports"
                                        :key="port.port"
                                        v-tooltip.top="port.desc || 'Без описания'"
                                        :class="{
                                            'border-orange-500!':
                                                vlanFilters.portsText.value &&
                                                (port.port
                                                    .toLocaleLowerCase()
                                                    .includes(vlanFilters.portsText.value.toLowerCase()) ||
                                                    port.desc
                                                        .toLocaleLowerCase()
                                                        .includes(vlanFilters.portsText.value.toLowerCase())),
                                        }"
                                        class="inline-flex max-w-[18rem] items-center gap-2 rounded-full border border-gray-200/80 bg-gray-50/80 px-3 py-1.5 dark:border-gray-700/80 dark:bg-gray-800/60"
                                    >
                                        <span
                                            class="shrink-0 font-mono text-sm font-semibold text-gray-900 dark:text-gray-100"
                                        >
                                            {{ port.port }}
                                        </span>
                                        <span
                                            v-if="port.desc"
                                            class="min-w-0 truncate text-xs text-gray-500 dark:text-gray-400"
                                        >
                                            {{ port.desc }}
                                        </span>
                                    </div>
                                </div>
                            </template>
                            <template #filter="{ filterModel, filterCallback }">
                                <InputText v-model="filterModel.value" type="text" fluid @input="filterCallback()" />
                            </template>
                        </Column>
                    </DataTable>
                </div>
            </div>

            <div
                v-else
                class="rounded-3xl border border-dashed border-gray-200/80 bg-white/70 px-4 py-10 text-center text-sm text-gray-500 dark:border-gray-700/80 dark:bg-gray-900/35 dark:text-gray-400"
            >
                Нет информации о VLAN для данного оборудования.
            </div>
        </div>
    </Dialog>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { AxiosResponse } from "axios";
import { FilterMatchMode } from "@primevue/core/api";

import errorFmt, { getErrorStatus } from "@/errorFmt";
import api from "@/services/api";

interface PortInfo {
    port: string;
    desc: string;
}

interface VlanInfo {
    ports: PortInfo[];
    vlan: number;
    datetime: string;
    desc: string;
}

interface VlanRow extends VlanInfo {
    vlanText: string;
    portsText: string;
}

const portNameCollator = new Intl.Collator("ru", { numeric: true, sensitivity: "base" });

function sortPortsByName(ports: PortInfo[]): PortInfo[] {
    return [...ports].sort((a, b) => portNameCollator.compare(a.port, b.port));
}

export default defineComponent({
    name: "DeviceVlanInfo",
    props: {
        deviceName: { required: true, type: String },
    },
    data() {
        return {
            showDialog: false,
            vlanInfo: null as VlanInfo[] | null,
            error: {
                status: null as number | null,
                msg: null as string | null,
            },
            vlanFilters: {
                global: { value: null as string | null, matchMode: FilterMatchMode.CONTAINS },
                vlanText: { value: null as string | null, matchMode: FilterMatchMode.CONTAINS },
                desc: { value: null as string | null, matchMode: FilterMatchMode.CONTAINS },
                portsText: { value: null as string | null, matchMode: FilterMatchMode.CONTAINS },
            },
        };
    },

    computed: {
        isLoading(): boolean {
            return this.vlanInfo === null && !this.error.status;
        },

        buttonTooltip(): string {
            if (this.error.status) return "Ошибка загрузки VLAN";
            if (this.isLoading) return "Загрузка VLAN";
            return `VLAN: ${this.vlanCount}`;
        },

        vlanRows(): VlanRow[] {
            return (this.vlanInfo || []).map((vlan) => {
                const ports = sortPortsByName(vlan.ports);

                return {
                    ...vlan,
                    ports,
                    vlanText: String(vlan.vlan),
                    portsText: ports.map((port) => `${port.port} ${port.desc || ""}`).join(" "),
                };
            });
        },

        vlanCount(): number {
            return this.vlanRows.length;
        },

        portsCount(): number {
            return this.vlanRows.reduce((total, vlan) => total + vlan.ports.length, 0);
        },

        latestFoundTime(): string {
            if (!this.vlanRows.length) return "-";

            const latestTimestamp = Math.max(...this.vlanRows.map((vlan) => new Date(vlan.datetime).getTime()));
            return this.formatTime(new Date(latestTimestamp).toISOString());
        },

        summaryMetrics(): { label: string; value: string | number; hint: string }[] {
            return [
                { label: "VLAN", value: this.vlanCount, hint: "Всего найдено" },
                { label: "Порты", value: this.portsCount, hint: "С привязкой к VLAN" },
                { label: "Обновлено", value: this.latestFoundTime, hint: "Последняя запись" },
            ];
        },
    },

    mounted() {
        api.get("/api/v1/devices/" + this.deviceName + "/vlan-info")
            .then((resp: AxiosResponse<VlanInfo[]>) => {
                this.vlanInfo = [...resp.data].sort((a, b) => a.vlan - b.vlan);
            })
            .catch((reason) => {
                this.error.status = getErrorStatus(reason) || null;
                this.error.msg = errorFmt(reason);
            });
    },

    methods: {
        openDialog() {
            this.showDialog = true;
        },

        formatPortsCount(count: number): string {
            if (count % 10 === 1 && count % 100 !== 11) return "порт";
            if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) return "порта";
            return "портов";
        },

        formatTime(datetime: string): string {
            const date = new Date(datetime);
            // Make a fuzzy time
            let delta = Math.round((Date.now() - date.getTime()) / 1000);
            let minute = 60;
            let hour = minute * 60;
            let fuzzy = "";
            if (delta < 30) {
                fuzzy = "Только что.";
            } else if (delta < minute) {
                fuzzy = delta + " сек. назад.";
            } else if (delta < 2 * minute) {
                fuzzy = "минуту назад.";
            } else if (delta < hour) {
                fuzzy = Math.floor(delta / minute) + " мин. назад.";
            }

            if (fuzzy.length) return fuzzy;

            return date.toLocaleString("ru", {
                year: "numeric",
                month: "long",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
            });
        },
    },
});
</script>
