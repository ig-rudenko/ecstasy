<template>
    <div class="mx-auto py-2 sm:py-6 lg:px-8">
        <div class="flex flex-col gap-4 sm:gap-6">
            <div class="flex flex-col gap-4 sm:gap-6 justify-center mx-auto max-w-7xl w-full sm:px-6 lg:px-8">
                <section
                    class="not-sm:py-25 not-sm:-my-25 relative overflow-hidden sm:rounded-4xl sm:border border-gray-200/70 dark:border-gray-700/70 dark:bg-gray-900/45 bg-white/80 backdrop-blur transition hover:-translate-y-0.5 delay-0 hover:bg-linear-to-br hover:from-transparent hover:via-transparent hover:to-indigo-500/10 hover:shadow-md"
                >
                    <div
                        class="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(99,102,241,0.14),transparent_25%),radial-gradient(circle_at_85%_20%,rgba(14,165,233,0.14),transparent_22%)]"
                    />
                    <div class="relative p-5 sm:p-8">
                        <div class="flex flex-col gap-8 xl:flex-row xl:items-start xl:justify-between">
                            <div class="max-w-4xl">
                                <h1
                                    class="mt-5 text-3xl font-semibold tracking-tight text-gray-900 dark:text-gray-100 sm:text-4xl"
                                >
                                    Поиск интерфейсов
                                </h1>

                                <p
                                    class="mt-3 max-w-3xl text-sm leading-7 text-gray-600 dark:text-gray-300 sm:text-base"
                                >
                                    Вы сможете найти интерфейсы оборудования по различным параметрам, если они были
                                    собраны ранее.
                                </p>
                            </div>

                            <div class="hidden xl:block w-56 shrink-0 opacity-95">
                                <img class="w-full" src="/img/search-description-2.svg" alt="Поиск интерфейсов" />
                            </div>
                        </div>
                    </div>
                </section>

                <section
                    class="sm:rounded-4xl sm:border border-gray-200/70 dark:border-gray-700/70 dark:bg-gray-900/45 bg-white/80 sm:p-6 backdrop-blur transition hover:-translate-y-0.5 delay-0 hover:bg-linear-to-br hover:from-transparent hover:via-transparent hover:to-indigo-500/10 hover:shadow-md"
                    :class="{
                        'sm:ring-2! ring-indigo-400/60! dark:ring-indigo-500/40!':
                            isRegexPattern || apiFilters.interfaceNameRegex || apiFilters.deviceNameRegex,
                    }"
                >
                    <div class="flex flex-col gap-4">
                        <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                            <!-- <label-->
                            <!--     for="isRegexPattern"-->
                            <!--     class="cursor-pointer inline-flex w-fit items-center gap-3 rounded-2xl border border-gray-200/80 bg-gray-50/80 px-3 py-2 text-sm text-gray-700 dark:border-gray-700/80 dark:bg-gray-800/60 dark:text-gray-300"-->
                            <!--     :class="{ 'opacity-50 cursor-not-allowed pointer-events-none': waitResult }"-->
                            <!-- >-->
                            <!--     <ToggleSwitch-->
                            <!--         v-model="isRegexPattern"-->
                            <!--         input-id="isRegexPattern"-->
                            <!--         :disabled="waitResult"-->
                            <!--     />-->
                            <!--     <span>Искать по регулярному выражению</span>-->
                            <!-- </label>-->

                            <div
                                v-show="isRegexPattern || apiFilters.interfaceNameRegex || apiFilters.deviceNameRegex"
                                class="text-sm not-sm:p-4 text-gray-500 dark:text-gray-400"
                            >
                                При поиске будет использовано регулярное выражение. Проверка шаблона:
                                <a
                                    href="https://regex101.com/"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    class="text-indigo-600 hover:underline dark:text-indigo-400"
                                >
                                    regex101.com
                                </a>
                            </div>
                        </div>

                        <InputGroup class="not-sm:px-4">
                            <SearchInput
                                @submit_input="searchInterfaces"
                                @update:modelValue="(v: string) => (pattern = v)"
                                :init-search="pattern"
                                :active-mode="true"
                                input-class="rounded-r-none"
                                placeholder="Введите строку для поиска в описании интерфейса"
                            />
                            <InputGroupAddon class="rounded-r-2xl">
                                <RegExpButton
                                    :regexpEnabled="isRegexPattern"
                                    :disabled="waitResult"
                                    btnClass="border-none"
                                    class="w-12"
                                    @click="isRegexPattern = !isRegexPattern"
                                />
                            </InputGroupAddon>
                        </InputGroup>
                        <div class="flex flex-wrap items-center gap-2 not-sm:px-4">
                            <Button
                                type="button"
                                icon="pi pi-search"
                                label="Найти"
                                class="rounded-2xl! text-sm sm:text-base"
                                :loading="waitResult"
                                @click="searchInterfaces"
                            />
                            <Button
                                type="button"
                                severity="secondary"
                                outlined
                                icon="pi pi-sliders-h"
                                :label="showAdvancedFilters ? 'Скрыть параметры' : 'Дополнительные параметры'"
                                :badge="additionalFiltersCount ? String(additionalFiltersCount) : undefined"
                                class="rounded-2xl! text-sm sm:text-base"
                                @click="showAdvancedFilters = !showAdvancedFilters"
                            />
                            <Button
                                v-if="hasActiveApiFilters"
                                type="button"
                                severity="secondary"
                                text
                                icon="pi pi-filter-slash"
                                label="Очистить параметры"
                                class="rounded-2xl! text-sm sm:text-base"
                                @click="clearApiFilters"
                            />
                        </div>

                        <div
                            v-if="showAdvancedFilters"
                            class="sm:rounded-3xl border border-gray-200/80 bg-gray-50/80 p-4 dark:border-gray-700/70 dark:bg-gray-800/45"
                        >
                            <div class="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_12rem_15rem]">
                                <div class="min-w-0">
                                    <label
                                        class="mb-1.5 block text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400"
                                        for="apiDeviceName"
                                        >Оборудование</label
                                    >
                                    <InputGroup>
                                        <InputText
                                            id="apiDeviceName"
                                            v-model.trim="apiFilters.deviceName"
                                            class="font-mono placeholder:opacity-50 text-sm sm:text-base rounded-l-2xl"
                                            placeholder="Имя устройства"
                                            :disabled="waitResult"
                                        />
                                        <RegExpButton
                                            :regexpEnabled="apiFilters.deviceNameRegex"
                                            :disabled="waitResult"
                                            @click="apiFilters.deviceNameRegex = !apiFilters.deviceNameRegex"
                                            class="w-12 rounded-r-2xl"
                                        />
                                    </InputGroup>
                                </div>
                                <div class="min-w-0">
                                    <label
                                        class="mb-1.5 block text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400"
                                        for="apiInterfaceName"
                                        >Название интерфейса</label
                                    >
                                    <InputGroup>
                                        <InputText
                                            id="apiInterfaceName"
                                            v-model.trim="apiFilters.interfaceName"
                                            class="font-mono placeholder:opacity-50 text-sm sm:text-base rounded-l-2xl"
                                            placeholder="Gi0/1"
                                            :disabled="waitResult"
                                        />
                                        <RegExpButton
                                            :regexpEnabled="apiFilters.interfaceNameRegex"
                                            :disabled="waitResult"
                                            @click="apiFilters.interfaceNameRegex = !apiFilters.interfaceNameRegex"
                                            class="w-12 rounded-r-2xl"
                                        />
                                    </InputGroup>
                                </div>
                                <div class="min-w-0">
                                    <label
                                        class="mb-1.5 block text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400"
                                        for="apiInterfaceStatus"
                                        >Статус</label
                                    >
                                    <Select
                                        id="apiInterfaceStatus"
                                        v-model="apiFilters.interfaceStatus"
                                        :options="statusOptions"
                                        placeholder="Все"
                                        class="w-full font-mono placeholder:opacity-50 text-sm sm:text-base rounded-2xl"
                                        :showClear="true"
                                        :disabled="waitResult"
                                    />
                                </div>
                                <label
                                    for="apiHasComment"
                                    class="sm:mt-3 inline-flex cursor-pointer items-center justify-center gap-3 rounded-2xl border border-gray-200/80 bg-white/80 px-3 py-2 text-sm text-gray-700 dark:border-gray-700/80 dark:bg-gray-900/45 dark:text-gray-300"
                                    :class="{ 'pointer-events-none cursor-not-allowed opacity-50': waitResult }"
                                >
                                    <ToggleSwitch
                                        v-model="apiFilters.hasComment"
                                        input-id="apiHasComment"
                                        :disabled="waitResult"
                                    />
                                    <span>Только с комментариями</span>
                                </label>
                            </div>

                            <div class="mt-4 grid gap-3 lg:grid-cols-3">
                                <div
                                    class="rounded-2xl border border-emerald-200/80 bg-emerald-50/70 p-3 dark:border-emerald-900/60 dark:bg-emerald-500/10"
                                >
                                    <div
                                        class="mb-2 flex items-center gap-2 text-sm font-semibold text-emerald-900 dark:text-emerald-100"
                                    >
                                        <i class="pi pi-check-circle" /><span>Найти VLAN</span>
                                    </div>
                                    <InputText
                                        v-model.trim="apiFilters.vlans"
                                        class="w-full font-mono placeholder:opacity-50 rounded-2xl"
                                        placeholder="10,20-30"
                                        :disabled="waitResult"
                                    />
                                </div>
                                <div
                                    class="rounded-2xl border border-sky-200/80 bg-sky-50/70 p-3 dark:border-sky-900/60 dark:bg-sky-500/10"
                                >
                                    <div
                                        class="mb-2 flex items-center gap-2 text-sm font-semibold text-sky-900 dark:text-sky-100"
                                    >
                                        <i class="pi pi-list-check" /><span>Все VLAN из диапазона</span>
                                    </div>
                                    <InputText
                                        v-model.trim="apiFilters.vlansSuperset"
                                        class="w-full font-mono placeholder:opacity-50 rounded-2xl"
                                        placeholder="1-4094"
                                        :disabled="waitResult"
                                    />
                                </div>
                                <div
                                    class="rounded-2xl border border-rose-200/80 bg-rose-50/70 p-3 dark:border-rose-900/60 dark:bg-rose-500/10"
                                >
                                    <div
                                        class="mb-2 flex items-center gap-2 text-sm font-semibold text-rose-900 dark:text-rose-100"
                                    >
                                        <i class="pi pi-ban" /><span>Исключить VLAN</span>
                                    </div>
                                    <InputText
                                        v-model.trim="apiFilters.vlansExclude"
                                        class="w-full font-mono placeholder:opacity-50 rounded-2xl"
                                        placeholder="100,200-210"
                                        :disabled="waitResult"
                                    />
                                </div>
                            </div>

                            <div class="mt-4 grid gap-3 lg:grid-cols-[minmax(0,22rem)_minmax(0,1fr)] lg:items-end">
                                <div class="min-w-0">
                                    <label
                                        class="mb-1.5 block text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400"
                                        for="apiDiscoveredAfter"
                                        >Обнаружено после</label
                                    >
                                    <DatePicker
                                        id="apiDiscoveredAfter"
                                        v-model="apiFilters.discoveredDatetimeGt"
                                        showIcon
                                        showTime
                                        show-clear
                                        hourFormat="24"
                                        dateFormat="dd.mm.yy"
                                        placeholder="Дата и время"
                                        inputClass="rounded-l-2xl"
                                        panel-class="rounded-2xl"
                                        class="w-full font-mono placeholder:opacity-50"
                                        :disabled="waitResult"
                                    />
                                </div>
                                <div class="text-sm leading-6 text-gray-500 dark:text-gray-400">
                                    Эти параметры отправляются на сервер. Фильтры в таблице ниже уточняют уже полученные
                                    строки.
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                <div
                    v-if="waitResult"
                    class="sm:rounded-4xl sm:border border-gray-200/70 bg-white/80 px-6 py-10 text-center backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/45"
                >
                    <p class="text-base text-gray-800 dark:text-gray-100 sm:text-lg">
                        Поиск по паттерну:
                        <code class="mx-1 rounded-lg bg-gray-100 px-2 py-0.5 font-mono text-sm dark:bg-gray-800">{{
                            pattern
                        }}</code>
                    </p>
                    <img class="mx-auto mt-6 h-50 object-contain" src="/img/load_desc.gif" alt="loading" />
                </div>
            </div>

            <template v-if="lastPattern">
                <section
                    v-if="interfaces.length"
                    class="lg:rounded-4xl md:border border-gray-200/70 bg-white/80 backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/45"
                >
                    <div class="flex flex-col gap-5">
                        <div class="flex flex-col gap-3 p-6 pb-1 lg:flex-row lg:items-start lg:justify-between">
                            <div>
                                <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">
                                    Результаты по паттерну
                                    <code class="ml-2 font-mono text-base text-indigo-700 dark:text-indigo-300">{{
                                        lastPattern
                                    }}</code>
                                </h2>
                                <p class="mt-1 text-sm font-mono text-gray-600 dark:text-gray-300">
                                    Найдено: {{ filteredInterfaces.length }}
                                </p>
                            </div>

                            <div class="flex flex-wrap items-center gap-2">
                                <Button
                                    severity="success"
                                    @click="exportCSV"
                                    icon="pi pi-file-excel"
                                    outlined
                                    label="CSV"
                                    class="rounded-2xl!"
                                />
                                <Button
                                    v-if="hasActiveFilters"
                                    severity="secondary"
                                    outlined
                                    icon="pi pi-filter-slash"
                                    label="Сбросить"
                                    class="rounded-2xl!"
                                    @click="clearTableState"
                                />
                            </div>
                        </div>

                        <div class="backdrop-blur overflow-hidden">
                            <div class="px-4 sm:px-4 pb-2">
                                <div class="flex flex-col gap-4">
                                    <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                                        <div
                                            class="rounded-2xl sm:border border-gray-200/80 bg-gray-50/80 px-3 py-2 text-sm font-mono text-gray-600 dark:border-gray-700/80 dark:bg-gray-800/60 dark:text-gray-300"
                                        >
                                            {{ filteredInterfaces.length }} строк
                                        </div>
                                        <div class="w-full lg:w-24">
                                            <Select
                                                v-model="rows"
                                                :options="rowsPerPageOptions"
                                                class="w-full rounded-2xl text-sm sm:text-base"
                                            />
                                        </div>
                                    </div>

                                    <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
                                        <div class="min-w-0">
                                            <div
                                                class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400"
                                            >
                                                Оборудование
                                            </div>
                                            <InputText
                                                v-model="filters.device"
                                                class="w-full rounded-2xl text-sm sm:text-base"
                                                placeholder="Поиск по имени"
                                            />
                                        </div>
                                        <div class="min-w-0">
                                            <div
                                                class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400"
                                            >
                                                Порт
                                            </div>
                                            <InputText
                                                v-model="filters.port"
                                                class="w-full rounded-2xl text-sm sm:text-base"
                                                placeholder="Поиск порта"
                                            />
                                        </div>
                                        <div class="min-w-0">
                                            <div
                                                class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400"
                                            >
                                                Статус
                                            </div>
                                            <Select
                                                v-model="filters.status"
                                                :options="statusOptions"
                                                placeholder="Все"
                                                class="w-full rounded-2xl text-sm sm:text-base"
                                                :showClear="true"
                                            />
                                        </div>
                                        <div class="min-w-0">
                                            <div
                                                class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400"
                                            >
                                                Описание
                                            </div>
                                            <InputText
                                                v-model="filters.description"
                                                class="w-full rounded-2xl text-sm sm:text-base"
                                                placeholder="Поиск"
                                            />
                                        </div>
                                        <div class="min-w-0">
                                            <div
                                                class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400"
                                            >
                                                Комментарии
                                            </div>
                                            <InputText
                                                v-model="filters.comments"
                                                class="w-full rounded-2xl text-sm sm:text-base"
                                                placeholder="Поиск"
                                            />
                                        </div>
                                        <div class="min-w-0">
                                            <div
                                                class="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400"
                                            >
                                                VLAN
                                            </div>
                                            <InputText
                                                v-model="filters.vlans"
                                                class="w-full rounded-2xl text-sm sm:text-base"
                                                placeholder="Поиск VLAN"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="overflow-x-auto mt-2">
                                <DataTable
                                    :value="filteredInterfaces"
                                    paginator
                                    :rows="rows"
                                    :first="page * rows"
                                    :rowsPerPageOptions="rowsPerPageOptions"
                                    :always-show-paginator="false"
                                    paginator-position="both"
                                    row-hover
                                    removableSort
                                    class="min-w-300 text-sm"
                                    @page="onPage"
                                    :pt="{
                                        column: {
                                            headerCell: {
                                                class: 'bg-gray-50/90 dark:bg-gray-900/80 text-xs uppercase text-gray-500 dark:text-gray-400',
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
                                        <div class="py-10 text-center">
                                            <div class="text-lg font-semibold text-gray-900 dark:text-gray-100">
                                                По фильтрам ничего не найдено
                                            </div>
                                            <div class="mt-1 text-sm text-gray-600 dark:text-gray-300">
                                                Измените фильтры или сбросьте их.
                                            </div>
                                        </div>
                                    </template>

                                    <Column field="device" header="Оборудование" sortable>
                                        <template #body="{ data }">
                                            <router-link
                                                :to="'/device/' + data.device"
                                                target="_blank"
                                                rel="noopener noreferrer"
                                            >
                                                <Button
                                                    text
                                                    icon="pi pi-box"
                                                    size="small"
                                                    class="rounded-2xl! max-w-full text-xs sm:text-base truncate"
                                                    :label="data.device"
                                                />
                                            </router-link>
                                        </template>
                                    </Column>

                                    <Column field="interface.name" header="Порт" sortable>
                                        <template #body="{ data }">
                                            <router-link
                                                :to="'/device/' + data.device + '?port=' + data.interface.name"
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                class="inline-flex items-center rounded-xl bg-indigo-100 px-3 py-1.5 font-mono text-xs sm:text-sm text-indigo-900 transition hover:bg-indigo-200 dark:bg-indigo-500/20 dark:text-indigo-100 dark:hover:bg-indigo-500/30"
                                            >
                                                {{ data.interface.name }}
                                            </router-link>
                                        </template>
                                    </Column>

                                    <Column field="interface.status" header="Статус" sortable>
                                        <template #body="{ data }">
                                            <div
                                                :class="statusClass(data.interface.status)"
                                                class="inline-flex max-w-16 min-w-full items-center justify-center gap-2 rounded-xl px-3 py-2 text-center text-xs sm:text-sm font-medium"
                                                v-tooltip="data.interface.verboseSavedTime"
                                            >
                                                <span>{{ data.interface.status }}</span>
                                                <i class="pi pi-clock text-xs" />
                                            </div>
                                        </template>
                                    </Column>

                                    <Column field="interface.description" header="Описание" sortable>
                                        <template #body="{ data }">
                                            <div
                                                class="max-w-160 whitespace-pre-wrap wrap-break-word font-mono text-sm leading-relaxed text-gray-800 dark:text-gray-200"
                                                v-html="markDescription(data.interface.description)"
                                            />
                                        </template>
                                    </Column>

                                    <Column header="Комментарии">
                                        <template #body="{ data }">
                                            <Comment
                                                :interface="getInterface(data)"
                                                :markedText="lastPattern"
                                                :device-name="data.device"
                                            />
                                        </template>
                                    </Column>

                                    <Column field="interface.vlans" header="VLAN" sortable>
                                        <template #body="{ data }">
                                            <button
                                                type="button"
                                                class="font-mono text-indigo-600 truncate transition hover:underline dark:text-indigo-400"
                                                @click="toggleVlansList($event, data.interface)"
                                            >
                                                {{ truncateVlans(data.interface.vlans) || "-" }}
                                            </button>
                                        </template>
                                    </Column>

                                    <Column field="interface.savedTime" header="Время обнаружения" sortable>
                                        <template #body="{ data }">
                                            <span class="font-mono truncate text-xs">{{
                                                new Date(data.interface.savedTime).toLocaleString()
                                            }}</span>
                                        </template>
                                    </Column>
                                </DataTable>
                            </div>
                        </div>
                    </div>
                </section>

                <div
                    v-else
                    class="sm:rounded-4xl sm:border border-dashed border-gray-200/80 bg-white/70 px-6 py-12 text-center backdrop-blur dark:border-gray-700/60 dark:bg-gray-900/30"
                >
                    <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100">
                        По паттерну
                        <code class="mx-1 rounded-lg bg-amber-100/90 px-2 py-0.5 font-mono dark:bg-amber-900/40">{{
                            lastPattern
                        }}</code>
                        совпадений нет
                    </h2>
                </div>
            </template>
        </div>
    </div>

    <Popover
        ref="vlansList"
        :pt="{
            root: {
                class: 'before:!hidden overflow-hidden rounded-2xl border border-gray-200/80 dark:border-gray-700/60 bg-white/95 dark:bg-gray-900/80 dark:backdrop-blur-xl shadow-lg dark:ring-1! dark:ring-white/5!',
            },
            content: { class: 'p-4! max-w-md' },
        }"
    >
        <div class="border-b border-gray-200/70 pb-3 text-xs text-gray-500 dark:border-gray-700/60 dark:text-gray-400">
            <i class="pi pi-clock me-2 text-sm" />
            {{ selectedVlansTime }}
        </div>
        <div class="mt-3 whitespace-pre-wrap break-all font-mono text-sm text-gray-800 dark:text-gray-100">
            {{ selectedVlans }}
        </div>
    </Popover>
</template>

<script lang="ts">
import { defineComponent } from "vue";

import Comment from "@/components/Comment.vue";
import SearchInput from "@/components/SearchInput.vue";
import { DeviceInterface, findInterfaces, InterfaceFinderQuery, InterfaceFinderResult } from "@/services/interfaces";
import { markText } from "@/formats.ts";
import RegExpButton from "@/pages/interfaceFinder/RegExpButton.vue";

interface ApiFilters {
    deviceName: string;
    deviceNameRegex: boolean;
    interfaceName: string;
    interfaceNameRegex: boolean;
    interfaceStatus: string | null;
    hasComment: boolean;
    vlans: string;
    vlansSuperset: string;
    vlansExclude: string;
    discoveredDatetimeGt: Date | null;
}

function emptyApiFilters(): ApiFilters {
    return {
        deviceName: "",
        deviceNameRegex: false,
        interfaceName: "",
        interfaceNameRegex: false,
        interfaceStatus: null,
        hasComment: false,
        vlans: "",
        vlansSuperset: "",
        vlansExclude: "",
        discoveredDatetimeGt: null,
    };
}
export default defineComponent({
    components: { RegExpButton, Comment, SearchInput },
    data() {
        return {
            interfaces: [] as InterfaceFinderResult[],
            pattern: "" as string,
            lastPattern: "" as string,
            isRegexPattern: false,
            waitResult: false,
            showAdvancedFilters: false,
            rows: 25,
            page: 0,
            rowsPerPageOptions: [10, 25, 50, 100],
            statusOptions: ["up", "down", "admin down", "noPresent", "notPresent", "dormant"],
            selectedVlans: "",
            selectedVlansTime: "",
            apiFilters: emptyApiFilters(),
            filters: {
                device: "",
                port: "",
                status: null as string | null,
                description: "",
                comments: "",
                vlans: "",
            },
        };
    },
    computed: {
        hasActiveFilters(): boolean {
            return Boolean(
                this.filters.device ||
                this.filters.port ||
                this.filters.status ||
                this.filters.description ||
                this.filters.comments ||
                this.filters.vlans
            );
        },
        additionalFiltersCount(): number {
            return [
                this.apiFilters.deviceName,
                this.apiFilters.interfaceName,
                this.apiFilters.interfaceStatus,
                this.apiFilters.hasComment ? "hasComment" : "",
                this.apiFilters.vlans,
                this.apiFilters.vlansSuperset,
                this.apiFilters.vlansExclude,
                this.apiFilters.discoveredDatetimeGt ? "discoveredDatetimeGt" : "",
            ].filter(Boolean).length;
        },
        hasActiveApiFilters(): boolean {
            return this.additionalFiltersCount > 0;
        },
        filteredInterfaces(): InterfaceFinderResult[] {
            const device = this.filters.device.trim().toLowerCase();
            const port = this.filters.port.trim().toLowerCase();
            const status = (this.filters.status || "").trim().toLowerCase();
            const description = this.filters.description.trim().toLowerCase();
            const comments = this.filters.comments.trim().toLowerCase();
            const vlans = this.filters.vlans.trim().toLowerCase();

            return this.interfaces.filter((item) => {
                const commentsText = item.comments
                    .map((comment) => comment.text)
                    .join(" ")
                    .toLowerCase();
                if (device && !item.device.toLowerCase().includes(device)) return false;
                if (port && !item.interface.name.toLowerCase().includes(port)) return false;
                if (status && item.interface.status.toLowerCase() !== status) return false;
                if (description && !item.interface.description.toLowerCase().includes(description)) return false;
                if (comments && !commentsText.includes(comments)) return false;
                if (vlans && !item.interface.vlans.toLowerCase().includes(vlans)) return false;
                return true;
            });
        },
    },
    watch: {
        filteredInterfaces() {
            if (this.page * this.rows >= this.filteredInterfaces.length) {
                this.page = 0;
            }
        },
        rows() {
            this.page = 0;
        },
    },
    mounted() {
        const routePattern =
            this.$route.query.desc_pattern_regex || this.$route.query.desc_pattern || this.$route.query.pattern;
        if (routePattern) {
            this.pattern = this.queryValue(routePattern);
            this.isRegexPattern = Boolean(this.$route.query.desc_pattern_regex || this.$route.query.is_regex === "1");
            this.hydrateApiFiltersFromRoute();
            this.showAdvancedFilters = this.hasActiveApiFilters;
            this.searchInterfaces();
        }
    },
    methods: {
        queryValue(value: unknown): string {
            if (Array.isArray(value)) return String(value[0] || "");
            return String(value || "");
        },
        queryDate(value: unknown): Date | null {
            const raw = this.queryValue(value);
            if (!raw) return null;
            const date = new Date(raw);
            return Number.isNaN(date.getTime()) ? null : date;
        },
        queryBool(value: unknown): boolean {
            return ["1", "true", "yes"].includes(this.queryValue(value).toLowerCase());
        },
        dateToQuery(value: Date | null): string | undefined {
            return value ? value.toISOString() : undefined;
        },
        hydrateApiFiltersFromRoute() {
            this.apiFilters.deviceName = this.queryValue(
                this.$route.query.device_name_regex || this.$route.query.device_name
            );
            this.apiFilters.deviceNameRegex = Boolean(this.$route.query.device_name_regex);
            this.apiFilters.interfaceName = this.queryValue(
                this.$route.query.interface_regex || this.$route.query.interface
            );
            this.apiFilters.interfaceNameRegex = Boolean(this.$route.query.interface_regex);
            this.apiFilters.interfaceStatus = this.queryValue(this.$route.query.interface_status) || null;
            this.apiFilters.hasComment = this.queryBool(this.$route.query.has_comment);
            this.apiFilters.vlans = this.queryValue(this.$route.query.vlans);
            this.apiFilters.vlansSuperset = this.queryValue(this.$route.query.vlans_superset);
            this.apiFilters.vlansExclude = this.queryValue(this.$route.query.vlans_exclude);
            this.apiFilters.discoveredDatetimeGt = this.queryDate(this.$route.query.discovered_datetime_gt);
        },
        getFinderQuery(): InterfaceFinderQuery {
            return {
                descriptionPattern: this.pattern.trim(),
                descriptionPatternRegex: this.isRegexPattern,
                deviceName: this.apiFilters.deviceName.trim() || undefined,
                deviceNameRegex: this.apiFilters.deviceNameRegex,
                interfaceName: this.apiFilters.interfaceName.trim() || undefined,
                interfaceNameRegex: this.apiFilters.interfaceNameRegex,
                interfaceStatus: this.apiFilters.interfaceStatus,
                hasComment: this.apiFilters.hasComment,
                vlans: this.apiFilters.vlans.trim() || undefined,
                vlansSuperset: this.apiFilters.vlansSuperset.trim() || undefined,
                vlansExclude: this.apiFilters.vlansExclude.trim() || undefined,
                discoveredDatetimeGt: this.dateToQuery(this.apiFilters.discoveredDatetimeGt),
            };
        },
        getRouteQuery(): Record<string, string> {
            const query: Record<string, string> = {};
            query[this.isRegexPattern ? "desc_pattern_regex" : "desc_pattern"] = this.pattern.trim();
            if (this.apiFilters.deviceName.trim()) {
                query[this.apiFilters.deviceNameRegex ? "device_name_regex" : "device_name"] =
                    this.apiFilters.deviceName.trim();
            }
            if (this.apiFilters.interfaceName.trim()) {
                query[this.apiFilters.interfaceNameRegex ? "interface_regex" : "interface"] =
                    this.apiFilters.interfaceName.trim();
            }
            if (this.apiFilters.interfaceStatus) query.interface_status = this.apiFilters.interfaceStatus;
            if (this.apiFilters.hasComment) query.has_comment = "1";
            if (this.apiFilters.vlans.trim()) query.vlans = this.apiFilters.vlans.trim();
            if (this.apiFilters.vlansSuperset.trim()) query.vlans_superset = this.apiFilters.vlansSuperset.trim();
            if (this.apiFilters.vlansExclude.trim()) query.vlans_exclude = this.apiFilters.vlansExclude.trim();
            if (this.apiFilters.discoveredDatetimeGt) {
                query.discovered_datetime_gt = this.apiFilters.discoveredDatetimeGt.toISOString();
            }
            return query;
        },
        clearApiFilters() {
            this.apiFilters = emptyApiFilters();
        },
        getInterface(data: InterfaceFinderResult): DeviceInterface {
            return {
                name: data.interface.name,
                description: data.interface.description,
                status: data.interface.status,
                vlans: [],
                comments: data.comments,
            };
        },
        searchInterfaces() {
            if (this.pattern.trim().length < 2) return;
            this.waitResult = true;
            this.page = 0;

            this.$router.replace({ query: this.getRouteQuery() });

            findInterfaces(this.getFinderQuery())
                .then(
                    (data) => {
                        this.interfaces = data;
                        this.lastPattern = this.pattern;
                        this.waitResult = false;
                    },
                    () => (this.waitResult = false)
                )
                .catch(() => (this.waitResult = false));
        },
        markDescription(desc: string): string {
            return markText(desc, this.lastPattern);
        },
        statusClass(status: string): string {
            const normalized = status.toLowerCase();
            if (normalized === "admin down") return "bg-red-200 text-red-950 dark:bg-red-500/20 dark:text-red-100";
            if (normalized === "notpresent" || normalized === "nopresent")
                return "bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-100";
            if (normalized === "dormant") return "bg-amber-100 text-amber-950 dark:bg-amber-500/20 dark:text-amber-100";
            if (normalized !== "down")
                return "bg-emerald-300 text-emerald-950 dark:bg-emerald-500/20 dark:text-emerald-100";
            return "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-200";
        },
        truncateVlans(vlans: string): string {
            if (vlans.length > 24) return vlans.slice(0, 22) + "...";
            return vlans;
        },
        clearTableState() {
            this.filters.device = "";
            this.filters.port = "";
            this.filters.status = null;
            this.filters.description = "";
            this.filters.comments = "";
            this.filters.vlans = "";
            this.page = 0;
        },
        onPage(event: { page: number; rows: number }) {
            this.page = event.page;
            this.rows = event.rows;
        },
        toggleVlansList(event: Event, intf: { vlans: string; vlansSavedTime: string }) {
            this.selectedVlans = intf.vlans;
            this.selectedVlansTime = new Date(intf.vlansSavedTime).toLocaleString();
            (this.$refs.vlansList as { toggle: (e: Event) => void }).toggle(event);
        },
        exportCSV() {
            const header = ["device", "port", "status", "description", "comments", "vlans"];
            const lines = [header.join(",")];

            for (const item of this.filteredInterfaces) {
                const comments = item.comments.map((comment) => comment.text).join(" | ");
                const row = [
                    item.device,
                    item.interface.name,
                    item.interface.status,
                    item.interface.description,
                    comments,
                    item.interface.vlans,
                ].map((value) => `"${String(value ?? "").replaceAll('"', '""')}"`);
                lines.push(row.join(","));
            }

            const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" });
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = "interface-finder.csv";
            link.click();
            URL.revokeObjectURL(url);
        },
    },
});
</script>
