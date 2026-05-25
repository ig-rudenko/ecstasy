<script setup lang="ts">
import DiscoveryCandidatesFilters from "@/pages/discovery/components/DiscoveryCandidatesFilters.vue";
import DiscoveryCandidatesTable from "@/pages/discovery/components/DiscoveryCandidatesTable.vue";
import DiscoveryProfilesTable from "@/pages/discovery/components/DiscoveryProfilesTable.vue";
import DiscoveryRunsTable from "@/pages/discovery/components/DiscoveryRunsTable.vue";
import DiscoveryProfileDialog from "@/pages/discovery/components/DiscoveryProfileDialog.vue";
import DiscoveryAcceptDialog from "@/pages/discovery/components/DiscoveryAcceptDialog.vue";
import { useDiscoveryPage } from "@/pages/discovery/useDiscoveryPage";

const {
    activeTab,
    lookups,
    profiles,
    runs,
    candidates,
    runsTotal,
    candidatesTotal,
    runsPage,
    candidatesPage,
    selectedCandidateIds,
    candidateStatus,
    candidateSearch,
    candidateVendor,
    loadingProfiles,
    loadingRuns,
    loadingCandidates,
    creatingProfile,
    launchingProfileId,
    deletingProfileId,
    deletingRunId,
    deletingCandidateId,
    editingProfile,
    profileDialogVisible,
    acceptDialogVisible,
    selectedCandidate,
    profileForm,
    acceptForm,
    statusOptions,
    protocolOptions,
    portScanProtocolOptions,
    cmdProtocolOptions,
    readyCandidatesCount,
    activeRunsCount,
    candidateVendorOptions,
    resetProfileForm,
    openEditProfileDialog,
    loadRuns,
    loadCandidates,
    refreshCurrentData,
    saveProfile,
    launchRun,
    confirmDeleteProfile,
    confirmDeleteRun,
    confirmDeleteCandidate,
    openAcceptDialog,
    quickAcceptCandidate,
    ignoreCandidate,
    setSelectedCandidateIds,
    setCandidateSearch,
    setCandidateStatus,
    setCandidateVendor,
    confirmDeleteSelectedCandidates,
    confirmQuickAcceptSelectedCandidates,
    acceptCandidate,
    switchTab,
} = useDiscoveryPage();
</script>

<template>
    <ConfirmPopup />

    <main class="mx-auto max-w-375 px-2 py-2 sm:px-6 sm:py-8 lg:px-8">
        <div class="flex flex-col gap-6">
            <section
                class="rounded-3xl border border-gray-200/70 bg-white/80 p-5 shadow-[0_20px_70px_-45px_rgba(15,23,42,0.35)] backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/45 sm:rounded-4xl sm:p-7"
            >
                <div class="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
                    <div>
                        <div class="flex items-center gap-3">
                            <div
                                class="flex h-12 w-12 items-center justify-center rounded-2xl bg-sky-50 text-sky-700 ring-1 ring-sky-100 dark:bg-sky-950/40 dark:text-sky-200 dark:ring-sky-900/60"
                            >
                                <i class="pi pi-compass text-xl" />
                            </div>
                            <div>
                                <h1 class="text-2xl font-semibold text-gray-900 dark:text-gray-100 sm:text-3xl">
                                    Auto Discovery
                                </h1>
                                <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                                    Профили сканирования, фоновые запуски и найденные кандидаты
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="grid gap-3 sm:grid-cols-3 xl:min-w-160">
                        <div
                            class="rounded-2xl border border-gray-200/80 bg-gray-50/80 px-4 py-3 dark:border-gray-700/80 dark:bg-gray-800/60"
                        >
                            <div class="text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">Профили</div>
                            <div class="mt-1 text-2xl font-semibold text-gray-900 dark:text-gray-100">
                                {{ profiles.length }}
                            </div>
                        </div>
                        <div
                            class="rounded-2xl border border-gray-200/80 bg-gray-50/80 px-4 py-3 dark:border-gray-700/80 dark:bg-gray-800/60"
                        >
                            <div class="text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">Активные</div>
                            <div class="mt-1 text-2xl font-semibold text-sky-700 dark:text-sky-200">
                                {{ activeRunsCount }}
                            </div>
                        </div>
                        <div
                            class="rounded-2xl border border-gray-200/80 bg-gray-50/80 px-4 py-3 dark:border-gray-700/80 dark:bg-gray-800/60"
                        >
                            <div class="text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">Ready</div>
                            <div class="mt-1 text-2xl font-semibold text-emerald-700 dark:text-emerald-300">
                                {{ readyCandidatesCount }}
                            </div>
                        </div>
                    </div>
                </div>

                <div class="mt-6 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                    <div class="flex flex-wrap gap-2" role="tablist" aria-label="Discovery sections">
                        <Button
                            icon="pi pi-sliders-h"
                            label="Профили"
                            :outlined="activeTab !== 'profiles'"
                            class="rounded-2xl!"
                            @click="switchTab('profiles')"
                        />
                        <Button
                            icon="pi pi-history"
                            label="Запуски"
                            :outlined="activeTab !== 'runs'"
                            severity="secondary"
                            class="rounded-2xl!"
                            @click="switchTab('runs')"
                        />
                        <Button
                            icon="pi pi-list-check"
                            label="Кандидаты"
                            :outlined="activeTab !== 'candidates'"
                            severity="secondary"
                            class="rounded-2xl!"
                            @click="switchTab('candidates')"
                        />
                    </div>

                    <div class="flex flex-wrap gap-2">
                        <Button
                            icon="pi pi-plus"
                            label="Новый профиль"
                            class="rounded-2xl!"
                            @click="
                                resetProfileForm();
                                profileDialogVisible = true;
                            "
                        />
                        <Button
                            icon="pi pi-refresh"
                            label="Обновить"
                            severity="secondary"
                            outlined
                            class="rounded-2xl!"
                            :loading="loadingProfiles || loadingRuns || loadingCandidates"
                            @click="refreshCurrentData"
                        />
                    </div>
                </div>
            </section>

            <section
                v-if="activeTab === 'profiles'"
                class="rounded-3xl border border-gray-200/70 bg-white/80 p-4 backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/45 sm:rounded-4xl sm:p-6"
            >
                <DiscoveryProfilesTable
                    :profiles="profiles"
                    :loading="loadingProfiles"
                    :deviceGroups="lookups.deviceGroups"
                    :authGroups="lookups.authGroups"
                    :launchingProfileId="launchingProfileId"
                    :deletingProfileId="deletingProfileId"
                    @edit="openEditProfileDialog"
                    @launch="launchRun"
                    @delete="confirmDeleteProfile"
                />
            </section>

            <section
                v-if="activeTab === 'runs'"
                class="rounded-3xl border border-gray-200/70 bg-white/80 p-4 backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/45 sm:rounded-4xl sm:p-6"
            >
                <DiscoveryRunsTable
                    :runs="runs"
                    :profiles="profiles"
                    :loading="loadingRuns"
                    :deletingRunId="deletingRunId"
                    @delete="confirmDeleteRun"
                />

                <Paginator
                    v-if="runsTotal > 100"
                    :rows="100"
                    :totalRecords="runsTotal"
                    :first="(runsPage - 1) * 100"
                    class="mt-4"
                    @page="(event: any) => loadRuns(event.page + 1)"
                />
            </section>

            <section
                v-if="activeTab === 'candidates'"
                class="rounded-3xl border border-gray-200/70 bg-white/80 p-4 backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/45 sm:rounded-4xl sm:p-6"
            >
                <DiscoveryCandidatesFilters
                    :candidateSearch="candidateSearch"
                    :candidateStatus="candidateStatus"
                    :candidateVendor="candidateVendor"
                    :statusOptions="statusOptions"
                    :vendorOptions="candidateVendorOptions"
                    :loading="loadingCandidates"
                    @update:candidateSearch="setCandidateSearch"
                    @update:candidateStatus="setCandidateStatus"
                    @update:candidateVendor="setCandidateVendor"
                    @search="loadCandidates(1)"
                />

                <DiscoveryCandidatesTable
                    :candidates="candidates"
                    :loading="loadingCandidates"
                    :deletingCandidateId="deletingCandidateId"
                    :selectedIds="selectedCandidateIds"
                    @update:selectedIds="setSelectedCandidateIds"
                    @accept="openAcceptDialog"
                    @quick-accept="quickAcceptCandidate"
                    @ignore="ignoreCandidate"
                    @delete="confirmDeleteCandidate"
                    @delete-selected="confirmDeleteSelectedCandidates"
                    @quick-accept-selected="confirmQuickAcceptSelectedCandidates"
                />

                <Paginator
                    v-if="candidatesTotal > 100"
                    :rows="100"
                    :totalRecords="candidatesTotal"
                    :first="(candidatesPage - 1) * 100"
                    class="mt-4"
                    @page="(event: any) => loadCandidates(event.page + 1)"
                />
            </section>
        </div>
    </main>

    <DiscoveryProfileDialog
        v-model:visible="profileDialogVisible"
        :isEditMode="Boolean(editingProfile)"
        :creatingProfile="creatingProfile"
        :form="profileForm"
        :deviceGroups="lookups.deviceGroups"
        :authGroups="lookups.authGroups"
        :protocolOptions="protocolOptions"
        :portScanProtocolOptions="portScanProtocolOptions"
        :cmdProtocolOptions="cmdProtocolOptions"
        @save="saveProfile"
    />

    <DiscoveryAcceptDialog
        v-model:visible="acceptDialogVisible"
        :selectedCandidate="selectedCandidate"
        :form="acceptForm"
        :deviceGroups="lookups.deviceGroups"
        :authGroups="lookups.authGroups"
        :portScanProtocolOptions="portScanProtocolOptions"
        :cmdProtocolOptions="cmdProtocolOptions"
        @accept="acceptCandidate"
    />
</template>
