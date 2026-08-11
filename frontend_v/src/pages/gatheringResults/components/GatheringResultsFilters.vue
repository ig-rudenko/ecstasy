<script setup lang="ts">
import type { GatheringResultFilters, GatheringResultLookups } from "@/types/gatheringResults";

defineProps<{
    lookups: GatheringResultLookups;
    loading: boolean;
}>();

const filters = defineModel<GatheringResultFilters>({ required: true });
const emit = defineEmits<{
    apply: [];
    reset: [];
}>();

const taskStatusOptions = [
    { label: "Выполняется", value: "RUNNING" },
    { label: "Успешно", value: "SUCCESS" },
    { label: "Частично", value: "PARTIAL" },
    { label: "Ошибка", value: "FAILURE" },
];

const resultStatusOptions = [
    { label: "Выполняется", value: "RUNNING" },
    { label: "Успешно", value: "SUCCESS" },
    { label: "Пропущено", value: "SKIPPED" },
    { label: "Ошибка", value: "FAILURE" },
];
</script>

<template>
    <form class="space-y-5" @submit.prevent="emit('apply')">
        <div>
            <div class="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-200">
                <i class="pi pi-server text-sky-600" />
                Оборудование
            </div>
            <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                <FloatLabel variant="on">
                    <Select
                        v-model="filters.deviceGroup"
                        inputId="gathering-device-group"
                        :options="lookups.device_groups"
                        optionLabel="name"
                        optionValue="id"
                        showClear
                        class="rounded-2xl"
                        fluid
                    />
                    <label for="gathering-device-group" class="text-xs sm:text-base">Группа</label>
                </FloatLabel>
                <FloatLabel variant="on">
                    <InputText v-model="filters.deviceName" class="rounded-2xl" id="gathering-device-name" fluid />
                    <label for="gathering-device-name">Имя оборудования</label>
                </FloatLabel>
                <FloatLabel variant="on">
                    <Select
                        v-model="filters.vendor"
                        inputId="gathering-vendor"
                        :options="lookups.vendors"
                        filter
                        showClear
                        class="rounded-2xl"
                        fluid
                    />
                    <label for="gathering-vendor">Вендор</label>
                </FloatLabel>
                <FloatLabel variant="on">
                    <Select
                        v-model="filters.model"
                        inputId="gathering-model"
                        :options="lookups.models"
                        filter
                        showClear
                        class="rounded-2xl"
                        fluid
                    />
                    <label for="gathering-model">Модель</label>
                </FloatLabel>
            </div>
        </div>

        <Divider />

        <div>
            <div class="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-200">
                <i class="pi pi-clock text-indigo-600" />
                Фильтр периодической задачи
            </div>
            <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                <FloatLabel variant="on">
                    <Select
                        v-model="filters.taskStatus"
                        inputId="gathering-task-status"
                        :options="taskStatusOptions"
                        optionLabel="label"
                        optionValue="value"
                        showClear
                        class="rounded-2xl"
                        fluid
                    />
                    <label for="gathering-task-status">Статус запуска</label>
                </FloatLabel>
                <FloatLabel variant="on">
                    <Select
                        v-model="filters.taskName"
                        inputId="gathering-task-name"
                        :options="lookups.task_names"
                        filter
                        showClear
                        class="rounded-2xl"
                        fluid
                    />
                    <label for="gathering-task-name">Имя задачи</label>
                </FloatLabel>
                <FloatLabel variant="on">
                    <DatePicker
                        v-model="filters.taskStartedAfter"
                        inputId="gathering-task-after"
                        dateFormat="dd.mm.yy"
                        showTime
                        hourFormat="24"
                        showButtonBar
                        fluid
                        input-class="rounded-2xl"
                    />
                    <label for="gathering-task-after">Запуск от</label>
                </FloatLabel>
                <FloatLabel variant="on">
                    <DatePicker
                        v-model="filters.taskStartedBefore"
                        inputId="gathering-task-before"
                        dateFormat="dd.mm.yy"
                        showTime
                        hourFormat="24"
                        showButtonBar
                        fluid
                        input-class="rounded-2xl"
                    />
                    <label for="gathering-task-before">Запуск до</label>
                </FloatLabel>
            </div>
        </div>

        <Divider />

        <div>
            <div class="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-200">
                <i class="pi pi-list-check text-emerald-600" />
                Фильтр результата периодической задачи
            </div>
            <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                <FloatLabel variant="on">
                    <Select
                        v-model="filters.resultStatus"
                        inputId="gathering-result-status"
                        :options="resultStatusOptions"
                        optionLabel="label"
                        optionValue="value"
                        showClear
                        class="rounded-2xl"
                        fluid
                    />
                    <label for="gathering-result-status">Статус результата</label>
                </FloatLabel>
                <FloatLabel variant="on">
                    <Select
                        v-model="filters.errorType"
                        inputId="gathering-error-type"
                        :options="lookups.error_types"
                        filter
                        showClear
                        class="rounded-2xl"
                        fluid
                    />
                    <label for="gathering-error-type">Тип ошибки</label>
                </FloatLabel>
                <FloatLabel variant="on">
                    <DatePicker
                        v-model="filters.resultStartedAfter"
                        inputId="gathering-result-after"
                        dateFormat="dd.mm.yy"
                        showTime
                        hourFormat="24"
                        showButtonBar
                        input-class="rounded-2xl"
                        fluid
                    />
                    <label for="gathering-result-after">Опрос от</label>
                </FloatLabel>
                <FloatLabel variant="on">
                    <DatePicker
                        v-model="filters.resultStartedBefore"
                        inputId="gathering-result-before"
                        dateFormat="dd.mm.yy"
                        showTime
                        hourFormat="24"
                        showButtonBar
                        input-class="rounded-2xl"
                        fluid
                    />
                    <label for="gathering-result-before">Опрос до</label>
                </FloatLabel>
                <FloatLabel variant="on" class="xl:col-span-2">
                    <InputText v-model="filters.errorMessage" class="rounded-2xl" id="gathering-error-message" fluid />
                    <label for="gathering-error-message">Текст ошибки</label>
                </FloatLabel>
            </div>
        </div>

        <div class="flex flex-wrap justify-end gap-2">
            <Button
                type="button"
                label="Сбросить"
                icon="pi pi-times"
                severity="secondary"
                text
                class="rounded-2xl"
                @click="emit('reset')"
            />
            <Button type="submit" label="Применить" class="rounded-2xl" icon="pi pi-filter" :loading="loading" />
        </div>
    </form>
</template>
