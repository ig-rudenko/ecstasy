<script setup lang="ts">
import { DiscoveryLookupItem, DiscoveryProfile } from "@/services/discovery";

defineProps<{
    profiles: DiscoveryProfile[];
    loading: boolean;
    deviceGroups: DiscoveryLookupItem[];
    authGroups: DiscoveryLookupItem[];
    launchingProfileId: number | null;
    deletingProfileId: number | null;
}>();

const emit = defineEmits<{
    (e: "edit", profile: DiscoveryProfile): void;
    (e: "launch", profile: DiscoveryProfile, dryRun: boolean): void;
    (e: "delete", event: MouseEvent, profile: DiscoveryProfile): void;
}>();

function getLookupName(items: DiscoveryLookupItem[], id: number | null): string {
    return items.find((item) => item.id === id)?.name || "—";
}
</script>

<template>
    <div
        class="overflow-hidden rounded-[1.75rem] border border-gray-200/70 bg-white/70 backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/40"
    >
        <div class="overflow-x-auto">
            <table class="min-w-240 w-full text-sm">
                <thead class="border-b border-gray-200/70 bg-gray-50/80 dark:border-gray-700/70 dark:bg-gray-900/70">
                    <tr class="text-xs uppercase tracking-wide text-gray-600 dark:text-gray-300">
                        <th class="px-4 py-3 text-left font-semibold">Профиль</th>
                        <th class="px-4 py-3 text-left font-semibold">Группа</th>
                        <th class="px-4 py-3 text-left font-semibold">Auth</th>
                        <th class="px-4 py-3 text-left font-semibold">Discovery</th>
                        <th class="px-4 py-3 text-left font-semibold">Авто</th>
                        <th class="px-4 py-3 text-left font-semibold">Новое оборудование</th>
                        <th class="px-4 py-3 text-right font-semibold">Действия</th>
                    </tr>
                </thead>
                <tbody>
                    <tr
                        v-for="profile in profiles"
                        :key="profile.id"
                        class="border-b border-gray-200/60 transition hover:bg-white/70 dark:border-gray-700/60 dark:hover:bg-gray-900/50"
                    >
                        <td class="px-4 py-3">
                            <div class="font-semibold text-gray-900 dark:text-gray-100">{{ profile.name }}</div>
                            <div class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                                {{ profile.networks.join(", ") }}
                            </div>
                        </td>
                        <td class="px-4 py-3">{{ getLookupName(deviceGroups, profile.deviceGroup) }}</td>
                        <td class="px-4 py-3">
                            <div class="flex flex-wrap gap-1">
                                <Tag
                                    v-for="authId in profile.authGroups"
                                    :key="authId"
                                    severity="secondary"
                                    :value="getLookupName(authGroups, authId)"
                                />
                                <span v-if="!profile.authGroups.length" class="text-sm text-gray-500">—</span>
                            </div>
                        </td>
                        <td class="px-4 py-3">
                            <div class="flex flex-wrap gap-1">
                                <Tag severity="info" :value="profile.portScanProtocol" />
                                <Tag severity="secondary" :value="profile.cmdProtocol" />
                                <Tag severity="contrast" :value="`${profile.snmpCommunitiesCount} SNMP`" />
                            </div>
                        </td>
                        <td class="px-4 py-3">
                            <Tag
                                :severity="profile.autoCreate ? 'success' : 'secondary'"
                                :value="profile.autoCreate ? `>= ${profile.autoCreateMinConfidence}` : 'выкл'"
                            />
                        </td>
                        <td class="px-4 py-3">
                            <Tag
                                :severity="profile.activateCreatedDevices ? 'success' : 'secondary'"
                                :value="profile.activateCreatedDevices ? 'активно' : 'неактивно'"
                            />
                        </td>
                        <td class="px-4 py-3">
                            <div class="flex flex-wrap justify-end gap-2">
                                <Button
                                    icon="pi pi-pencil"
                                    label="Изменить"
                                    size="small"
                                    severity="secondary"
                                    outlined
                                    class="rounded-2xl!"
                                    @click="emit('edit', profile)"
                                />
                                <Button
                                    icon="pi pi-play"
                                    label="Запуск"
                                    size="small"
                                    class="rounded-2xl!"
                                    :loading="launchingProfileId === profile.id"
                                    @click="emit('launch', profile, false)"
                                />
                                <Button
                                    icon="pi pi-eye"
                                    label="Dry"
                                    size="small"
                                    severity="secondary"
                                    outlined
                                    class="rounded-2xl!"
                                    :loading="launchingProfileId === profile.id"
                                    @click="emit('launch', profile, true)"
                                />
                                <Button
                                    icon="pi pi-trash"
                                    label="Удалить"
                                    size="small"
                                    severity="danger"
                                    outlined
                                    class="rounded-2xl!"
                                    :loading="deletingProfileId === profile.id"
                                    @click="(event: MouseEvent) => emit('delete', event, profile)"
                                />
                            </div>
                        </td>
                    </tr>
                    <tr v-if="!loading && !profiles.length">
                        <td colspan="7" class="px-4 py-10 text-center text-sm text-gray-500">
                            Профили discovery еще не созданы
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>
