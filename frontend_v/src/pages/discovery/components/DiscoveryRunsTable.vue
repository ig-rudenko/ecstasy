<script setup lang="ts">
import { computed } from "vue";
import { verboseDatetime } from "@/formats";
import { DiscoveryProfile, DiscoveryRun } from "@/services/discovery";

const props = defineProps<{
    runs: DiscoveryRun[];
    profiles: DiscoveryProfile[];
    loading: boolean;
    deletingRunId: number | null;
}>();

const emit = defineEmits<{
    (e: "delete", event: MouseEvent, run: DiscoveryRun): void;
}>();

const profileNameById = computed<Record<number, string>>(() => {
    const value: Record<number, string> = {};
    for (const profile of props.profiles) {
        value[profile.id] = profile.name;
    }
    return value;
});

function getProfileName(profileId: number): string {
    return profileNameById.value[profileId] || `#${profileId}`;
}

function getRunProgress(run: DiscoveryRun): number {
    if (!run.total) {
        return 0;
    }
    return Math.round((run.processed / run.total) * 100);
}

function statusClass(status: string): string {
    if (["SUCCESS", "READY", "CREATED"].includes(status)) {
        return "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200";
    }
    if (["FAILURE", "FAILED"].includes(status)) {
        return "bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200";
    }
    if (["DUPLICATE", "IGNORED", "REVOKED"].includes(status)) {
        return "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200";
    }
    if (["PROGRESS", "PENDING"].includes(status)) {
        return "bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-200";
    }
    return "bg-slate-100 text-slate-700 dark:bg-slate-800/70 dark:text-slate-200";
}
</script>

<template>
    <div
        class="overflow-hidden rounded-[1.75rem] border border-gray-200/70 bg-white/70 backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/40"
    >
        <div class="overflow-x-auto">
            <table class="min-w-220 w-full text-sm">
                <thead class="border-b border-gray-200/70 bg-gray-50/80 dark:border-gray-700/70 dark:bg-gray-900/70">
                    <tr class="text-xs uppercase tracking-wide text-gray-600 dark:text-gray-300">
                        <th class="px-4 py-3 text-left font-semibold">Запуск</th>
                        <th class="px-4 py-3 text-left font-semibold">Статус</th>
                        <th class="px-4 py-3 text-left font-semibold">Прогресс</th>
                        <th class="px-4 py-3 text-left font-semibold">Итоги</th>
                        <th class="px-4 py-3 text-left font-semibold">Время</th>
                        <th class="px-4 py-3 text-right font-semibold">Действия</th>
                    </tr>
                </thead>
                <tbody>
                    <tr
                        v-for="run in runs"
                        :key="run.id"
                        class="border-b border-gray-200/60 transition hover:bg-white/70 dark:border-gray-700/60 dark:hover:bg-gray-900/50"
                    >
                        <td class="px-4 py-3">
                            <div class="font-semibold text-gray-900 dark:text-gray-100">
                                {{ getProfileName(run.profileId) }}
                            </div>
                            <div class="mt-1 font-mono text-xs text-gray-500">{{ run.task_id || `#${run.id}` }}</div>
                        </td>
                        <td class="px-4 py-3">
                            <span
                                class="inline-flex rounded-full px-2 py-1 text-xs font-semibold"
                                :class="statusClass(run.status)"
                            >
                                {{ run.status }}
                            </span>
                        </td>
                        <td class="px-4 py-3">
                            <div class="min-w-40">
                                <div class="h-2 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
                                    <div
                                        class="h-full rounded-full bg-sky-600 dark:bg-sky-400"
                                        :style="{ width: `${getRunProgress(run)}%` }"
                                    />
                                </div>
                                <div class="mt-1 text-xs text-gray-500">
                                    {{ run.processed }}/{{ run.total }} · {{ getRunProgress(run) }}%
                                </div>
                            </div>
                        </td>
                        <td class="px-4 py-3">
                            <div class="flex flex-wrap gap-1">
                                <Tag severity="success" :value="`found ${run.found}`" />
                                <Tag severity="info" :value="`created ${run.created}`" />
                                <Tag severity="warn" :value="`skip ${run.skipped}`" />
                                <Tag v-if="run.errors" severity="danger" :value="`err ${run.errors}`" />
                            </div>
                        </td>
                        <td class="px-4 py-3">
                            <div class="text-sm text-gray-700 dark:text-gray-200">
                                {{ verboseDatetime(run.created_at) }}
                            </div>
                            <div class="text-xs text-gray-500">
                                {{ run.finished_at ? verboseDatetime(run.finished_at) : "в процессе" }}
                            </div>
                        </td>
                        <td class="px-4 py-3">
                            <div class="flex justify-end">
                                <Button
                                    icon="pi pi-trash"
                                    label="Удалить"
                                    size="small"
                                    severity="danger"
                                    outlined
                                    class="rounded-2xl!"
                                    :loading="deletingRunId === run.id"
                                    @click="(event: MouseEvent) => emit('delete', event, run)"
                                />
                            </div>
                        </td>
                    </tr>
                    <tr v-if="!loading && !runs.length">
                        <td colspan="6" class="px-4 py-10 text-center text-sm text-gray-500">
                            Запуски discovery не найдены
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>
