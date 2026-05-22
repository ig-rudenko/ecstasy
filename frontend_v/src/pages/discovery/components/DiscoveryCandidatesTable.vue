<script setup lang="ts">
import { computed } from "vue";
import { DiscoveryCandidate } from "@/services/discovery";
import { verboseDatetime } from "@/formats";

const props = defineProps<{
    candidates: DiscoveryCandidate[];
    loading: boolean;
    deletingCandidateId: number | null;
    selectedIds: number[];
}>();

const emit = defineEmits<{
    (e: "update:selectedIds", value: number[]): void;
    (e: "accept", candidate: DiscoveryCandidate): void;
    (e: "quick-accept", candidate: DiscoveryCandidate): void;
    (e: "ignore", candidate: DiscoveryCandidate): void;
    (e: "delete", event: MouseEvent, candidate: DiscoveryCandidate): void;
    (e: "delete-selected", event: MouseEvent): void;
    (e: "quick-accept-selected", event: MouseEvent): void;
}>();

const allSelected = computed<boolean>(() => {
    if (!props.candidates.length) {
        return false;
    }
    return props.candidates.every((candidate) => props.selectedIds.includes(candidate.id));
});

function toggleAll(value: boolean): void {
    if (!value) {
        emit("update:selectedIds", []);
        return;
    }
    emit(
        "update:selectedIds",
        props.candidates.map((candidate) => candidate.id)
    );
}

function toggleOne(candidateId: number, checked: boolean): void {
    if (checked) {
        if (props.selectedIds.includes(candidateId)) {
            return;
        }
        emit("update:selectedIds", [...props.selectedIds, candidateId]);
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

function statusClass(status: string): string {
    if (["READY", "CREATED", "SUCCESS"].includes(status)) {
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
</script>

<template>
    <div
        class="overflow-hidden rounded-[1.75rem] border border-gray-200/70 bg-white/70 backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/40"
    >
        <div class="border-b border-gray-200/70 p-3 dark:border-gray-700/70">
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
                    icon="pi pi-trash"
                    label="Удалить выбранные"
                    size="small"
                    severity="danger"
                    outlined
                    class="rounded-2xl!"
                    :disabled="!selectedIds.length || loading"
                    @click="(event: MouseEvent) => emit('delete-selected', event)"
                />
                <span class="text-xs text-gray-500 dark:text-gray-400">Выбрано: {{ selectedIds.length }}</span>
            </div>
        </div>

        <div class="overflow-x-auto">
            <table class="min-w-260 w-full text-sm">
                <thead class="border-b border-gray-200/70 bg-gray-50/80 dark:border-gray-700/70 dark:bg-gray-900/70">
                    <tr class="text-xs uppercase tracking-wide text-gray-600 dark:text-gray-300">
                        <th class="px-4 py-3 text-left font-semibold w-10">
                            <Checkbox :binary="true" :modelValue="allSelected" @update:modelValue="toggleAll" />
                        </th>
                        <th class="px-4 py-3 text-left font-semibold">Кандидат</th>
                        <th class="px-4 py-3 text-left font-semibold">Identity</th>
                        <th class="px-4 py-3 text-left font-semibold">Статус</th>
                        <th class="px-4 py-3 text-left font-semibold">Протоколы</th>
                        <th class="px-4 py-3 text-left font-semibold">Последний раз</th>
                        <th class="px-4 py-3 text-right font-semibold">Действия</th>
                    </tr>
                </thead>
                <tbody>
                    <tr
                        v-for="candidate in candidates"
                        :key="candidate.id"
                        class="border-b border-gray-200/60 transition hover:bg-white/70 dark:border-gray-700/60 dark:hover:bg-gray-900/50"
                    >
                        <td class="px-4 py-3">
                            <Checkbox
                                :binary="true"
                                :modelValue="isSelected(candidate.id)"
                                @update:modelValue="(value: boolean) => toggleOne(candidate.id, value)"
                            />
                        </td>
                        <td class="px-4 py-3">
                            <div class="font-semibold text-gray-900 dark:text-gray-100">
                                {{ candidate.name || candidate.ip }}
                            </div>
                            <div class="mt-1 font-mono text-xs text-gray-500">{{ candidate.ip }}</div>
                        </td>
                        <td class="px-4 py-3">
                            <div class="text-sm text-gray-800 dark:text-gray-200">
                                {{ [candidate.vendor, candidate.model].filter(Boolean).join(" · ") || "—" }}
                            </div>
                            <div class="mt-1 max-w-90 truncate text-xs text-gray-500">
                                {{
                                    candidate.serialNumber ||
                                    candidate.sysName ||
                                    candidate.sysDescr ||
                                    "без fingerprint"
                                }}
                            </div>
                        </td>
                        <td class="px-4 py-3">
                            <div class="flex flex-col gap-1">
                                <span
                                    class="inline-flex w-fit rounded-full px-2 py-1 text-xs font-semibold"
                                    :class="statusClass(candidate.status)"
                                >
                                    {{ candidate.status }}
                                </span>
                                <span class="text-xs text-gray-500">confidence {{ candidate.confidence }}</span>
                            </div>
                        </td>
                        <td class="px-4 py-3">
                            <div class="flex flex-wrap gap-1">
                                <Tag
                                    v-for="(enabled, protocol) in candidate.detectedProtocols"
                                    :key="protocol"
                                    :severity="enabled ? 'success' : 'secondary'"
                                    :value="protocol"
                                />
                            </div>
                        </td>
                        <td class="px-4 py-3">
                            <div class="text-sm text-gray-700 dark:text-gray-200">
                                {{ verboseDatetime(candidate.last_seen_at) }}
                            </div>
                            <div v-if="candidate.lastError" class="mt-1 max-w-80 truncate text-xs text-rose-600">
                                {{ candidate.lastError }}
                            </div>
                        </td>
                        <td class="px-4 py-3">
                            <div class="flex flex-wrap justify-end gap-2">
                                <Button
                                    v-if="candidate.status === 'READY' || candidate.status === 'NEW'"
                                    icon="pi pi-check"
                                    label="Принять"
                                    size="small"
                                    class="rounded-2xl!"
                                    @click="emit('accept', candidate)"
                                />
                                <Button
                                    v-if="candidate.status === 'READY' || candidate.status === 'NEW'"
                                    icon="pi pi-plus-circle"
                                    label="Быстро"
                                    size="small"
                                    severity="secondary"
                                    outlined
                                    class="rounded-2xl!"
                                    @click="emit('quick-accept', candidate)"
                                />
                                <Button
                                    v-if="candidate.status !== 'IGNORED' && candidate.status !== 'CREATED'"
                                    icon="pi pi-eye-slash"
                                    label="Игнор"
                                    size="small"
                                    severity="secondary"
                                    outlined
                                    class="rounded-2xl!"
                                    @click="emit('ignore', candidate)"
                                />
                                <Button
                                    icon="pi pi-trash"
                                    label="Удалить"
                                    size="small"
                                    severity="danger"
                                    outlined
                                    class="rounded-2xl!"
                                    :loading="deletingCandidateId === candidate.id"
                                    @click="(event: MouseEvent) => emit('delete', event, candidate)"
                                />
                            </div>
                        </td>
                    </tr>
                    <tr v-if="!loading && !candidates.length">
                        <td colspan="7" class="px-4 py-10 text-center text-sm text-gray-500">
                            По текущим фильтрам кандидаты не найдены
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>
