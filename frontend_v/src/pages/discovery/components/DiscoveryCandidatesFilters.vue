<script setup lang="ts">
defineProps<{
    candidateSearch: string;
    candidateStatus: string;
    candidateVendor: string;
    statusOptions: { label: string; value: string }[];
    vendorOptions: { label: string; value: string }[];
    loading: boolean;
}>();

const emit = defineEmits<{
    (e: "update:candidateSearch", value: string): void;
    (e: "update:candidateStatus", value: string): void;
    (e: "update:candidateVendor", value: string): void;
    (e: "search"): void;
}>();
</script>

<template>
    <div class="mb-5 grid gap-3 lg:grid-cols-[1fr_16rem_16rem_auto]">
        <IconField>
            <InputIcon class="pi pi-search" />
            <InputText
                :modelValue="candidateSearch"
                fluid
                placeholder="IP, имя или hostname"
                class="rounded-2xl"
                @update:modelValue="(value) => emit('update:candidateSearch', String(value || ''))"
                @keyup.enter="emit('search')"
            />
        </IconField>
        <Select
            :modelValue="candidateStatus"
            :options="statusOptions"
            optionLabel="label"
            optionValue="value"
            class="w-full rounded-2xl"
            @update:modelValue="(value) => emit('update:candidateStatus', String(value || ''))"
            @change="emit('search')"
        />
        <Select
            :modelValue="candidateVendor"
            :options="vendorOptions"
            optionLabel="label"
            optionValue="value"
            class="w-full rounded-2xl"
            @update:modelValue="(value) => emit('update:candidateVendor', String(value || ''))"
            @change="emit('search')"
        />
        <Button icon="pi pi-search" label="Найти" class="rounded-2xl!" :loading="loading" @click="emit('search')" />
    </div>
</template>
