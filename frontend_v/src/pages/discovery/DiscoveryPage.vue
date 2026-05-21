<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { useConfirm } from "primevue/useconfirm";
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";
import errorFmt from "@/errorFmt";
import { verboseDatetime } from "@/formats";
import { errorToast, successToast } from "@/services/my.toast";
import {
    acceptDiscoveryCandidate,
    AcceptCandidatePayload,
    createDiscoveryProfile,
    deleteDiscoveryCandidate,
    deleteDiscoveryProfile,
    deleteDiscoveryRun,
    DiscoveryCandidate,
    DiscoveryLookupItem,
    DiscoveryProfile,
    DiscoveryProfilePayload,
    DiscoveryRun,
    getDiscoveryCandidates,
    getDiscoveryLookups,
    getDiscoveryRun,
    getDiscoveryRuns,
    getDiscoveryProfiles,
    ignoreDiscoveryCandidate,
    patchDiscoveryCandidate,
    patchDiscoveryProfile,
    startDiscoveryRun,
} from "@/services/discovery";

type TabName = "profiles" | "runs" | "candidates";

const activeTab = ref<TabName>("profiles");
const lookups = reactive<{ deviceGroups: DiscoveryLookupItem[]; authGroups: DiscoveryLookupItem[] }>({
    deviceGroups: [],
    authGroups: [],
});

const profiles = ref<DiscoveryProfile[]>([]);
const runs = ref<DiscoveryRun[]>([]);
const candidates = ref<DiscoveryCandidate[]>([]);
const runsTotal = ref(0);
const candidatesTotal = ref(0);
const runsPage = ref(1);
const candidatesPage = ref(1);
const candidateStatus = ref("");
const candidateSearch = ref("");
const candidateVendor = ref("");
const loadingProfiles = ref(false);
const loadingRuns = ref(false);
const loadingCandidates = ref(false);
const creatingProfile = ref(false);
const launchingProfileId = ref<number | null>(null);
const deletingProfileId = ref<number | null>(null);
const deletingRunId = ref<number | null>(null);
const deletingCandidateId = ref<number | null>(null);
const editingProfile = ref<DiscoveryProfile | null>(null);
const profileDialogVisible = ref(false);
const acceptDialogVisible = ref(false);
const selectedCandidate = ref<DiscoveryCandidate | null>(null);
const confirm = useConfirm();
let runPollingTimer: number | null = null;

const profileForm = reactive({
    name: "",
    networks: "192.0.2.0/24",
    excludeIps: "",
    deviceGroup: null as number | null,
    authGroups: [] as number[],
    snmpCommunities: "",
    tryProtocols: ["ssh"] as string[],
    portScanProtocol: "snmp" as "snmp" | "telnet" | "ssh",
    cmdProtocol: "ssh" as "telnet" | "ssh",
    maxWorkers: 32,
    timeoutSeconds: 2,
    autoCreate: false,
    autoCreateMinConfidence: 70,
    isActive: true,
});

const acceptForm = reactive<AcceptCandidatePayload & { name: string }>({
    name: "",
    deviceGroup: null,
    authGroup: null,
    cmdProtocol: "ssh",
    portScanProtocol: "snmp",
    snmpCommunity: "",
    collectInterfaces: false,
});

const statusOptions = [
    { label: "Все", value: "" },
    { label: "Новые", value: "NEW" },
    { label: "Готовые", value: "READY" },
    { label: "Дубли", value: "DUPLICATE" },
    { label: "Созданные", value: "CREATED" },
    { label: "Игнор", value: "IGNORED" },
    { label: "Ошибки", value: "FAILED" },
];

const protocolOptions = [
    { label: "SSH", value: "ssh" },
    { label: "Telnet", value: "telnet" },
];

const portScanProtocolOptions = [
    { label: "SNMP", value: "snmp" },
    { label: "SSH", value: "ssh" },
    { label: "Telnet", value: "telnet" },
];

const cmdProtocolOptions = [
    { label: "SSH", value: "ssh" },
    { label: "Telnet", value: "telnet" },
];

const readyCandidatesCount = computed(
    () => candidates.value.filter((candidate) => candidate.status === "READY").length
);

const activeRunsCount = computed(() =>
    runs.value.filter((run) => ["PENDING", "PROGRESS"].includes(run.status)).length
);

const candidateVendors = computed(() => {
    const vendors = new Set(candidates.value.map((candidate) => candidate.vendor).filter(Boolean));
    return [...vendors].sort((left, right) => left.localeCompare(right)).map((vendor) => ({ label: vendor, value: vendor }));
});

function parseLines(value: string): string[] {
    return value
        .split(/\r?\n|,/)
        .map((item) => item.trim())
        .filter(Boolean);
}

function resetProfileForm(): void {
    editingProfile.value = null;
    profileForm.name = "";
    profileForm.networks = "192.0.2.0/24";
    profileForm.excludeIps = "";
    profileForm.deviceGroup = lookups.deviceGroups[0]?.id || null;
    profileForm.authGroups = [];
    profileForm.snmpCommunities = "";
    profileForm.tryProtocols = ["ssh"];
    profileForm.portScanProtocol = "snmp";
    profileForm.cmdProtocol = "ssh";
    profileForm.maxWorkers = 32;
    profileForm.timeoutSeconds = 2;
    profileForm.autoCreate = false;
    profileForm.autoCreateMinConfidence = 70;
    profileForm.isActive = true;
}

function fillProfileForm(profile: DiscoveryProfile): void {
    editingProfile.value = profile;
    profileForm.name = profile.name;
    profileForm.networks = profile.networks.join("\n");
    profileForm.excludeIps = profile.exclude_ips.join("\n");
    profileForm.deviceGroup = profile.deviceGroup;
    profileForm.authGroups = [...profile.authGroups];
    profileForm.snmpCommunities = "";
    profileForm.tryProtocols = [...profile.tryProtocols];
    profileForm.portScanProtocol = profile.portScanProtocol;
    profileForm.cmdProtocol = profile.cmdProtocol;
    profileForm.maxWorkers = profile.maxWorkers;
    profileForm.timeoutSeconds = profile.timeoutSeconds;
    profileForm.autoCreate = profile.autoCreate;
    profileForm.autoCreateMinConfidence = profile.autoCreateMinConfidence;
    profileForm.isActive = profile.isActive;
}

function openEditProfileDialog(profile: DiscoveryProfile): void {
    fillProfileForm(profile);
    profileDialogVisible.value = true;
}

function buildProfilePayload(includeEmptySnmp = true): DiscoveryProfilePayload {
    const payload: DiscoveryProfilePayload = {
        name: profileForm.name.trim(),
        networks: parseLines(profileForm.networks),
        exclude_ips: parseLines(profileForm.excludeIps),
        deviceGroup: profileForm.deviceGroup,
        authGroups: profileForm.authGroups,
        tryProtocols: profileForm.tryProtocols,
        portScanProtocol: profileForm.portScanProtocol,
        cmdProtocol: profileForm.cmdProtocol,
        maxWorkers: profileForm.maxWorkers,
        timeoutSeconds: profileForm.timeoutSeconds,
        autoCreate: profileForm.autoCreate,
        autoCreateMinConfidence: profileForm.autoCreateMinConfidence,
        isActive: profileForm.isActive,
    };
    const snmpCommunities = parseLines(profileForm.snmpCommunities);
    if (includeEmptySnmp || snmpCommunities.length) {
        payload.snmpCommunities = snmpCommunities;
    } else {
        delete (payload as Partial<DiscoveryProfilePayload>).snmpCommunities;
    }
    return payload;
}

async function loadLookups(): Promise<void> {
    try {
        const response = await getDiscoveryLookups();
        lookups.deviceGroups = response.deviceGroups;
        lookups.authGroups = response.authGroups;
        if (!profileForm.deviceGroup) {
            profileForm.deviceGroup = response.deviceGroups[0]?.id || null;
        }
    } catch (error: any) {
        errorToast("Не удалось загрузить справочники", errorFmt(error));
    }
}

async function loadProfiles(): Promise<void> {
    loadingProfiles.value = true;
    try {
        profiles.value = await getDiscoveryProfiles();
    } catch (error: any) {
        errorToast("Не удалось загрузить профили discovery", errorFmt(error));
    } finally {
        loadingProfiles.value = false;
    }
}

async function loadRuns(page = runsPage.value): Promise<void> {
    loadingRuns.value = true;
    try {
        const response = await getDiscoveryRuns(page);
        runs.value = response.results;
        runsTotal.value = response.count;
        runsPage.value = page;
        updateRunPolling();
    } catch (error: any) {
        errorToast("Не удалось загрузить запуски discovery", errorFmt(error));
    } finally {
        loadingRuns.value = false;
    }
}

async function loadCandidates(page = candidatesPage.value): Promise<void> {
    loadingCandidates.value = true;
    try {
        const response = await getDiscoveryCandidates({
            page,
            status: candidateStatus.value,
            search: candidateSearch.value,
            vendor: candidateVendor.value,
        });
        candidates.value = response.results;
        candidatesTotal.value = response.count;
        candidatesPage.value = page;
    } catch (error: any) {
        errorToast("Не удалось загрузить кандидатов discovery", errorFmt(error));
    } finally {
        loadingCandidates.value = false;
    }
}

async function refreshCurrentData(): Promise<void> {
    await Promise.all([loadProfiles(), loadRuns(runsPage.value), loadCandidates(candidatesPage.value)]);
}

async function saveProfile(): Promise<void> {
    if (!profileForm.name.trim()) {
        errorToast("Не заполнено имя", "Укажите имя профиля discovery.");
        return;
    }
    if (!profileForm.deviceGroup) {
        errorToast("Не выбрана группа", "Выберите группу оборудования.");
        return;
    }

    creatingProfile.value = true;
    try {
        if (editingProfile.value) {
            const profile = await patchDiscoveryProfile(editingProfile.value.id, buildProfilePayload(false));
            const index = profiles.value.findIndex((item) => item.id === profile.id);
            if (index >= 0) {
                profiles.value[index] = profile;
            }
            successToast("Профиль обновлен", profile.name);
        } else {
            const profile = await createDiscoveryProfile(buildProfilePayload(true));
            profiles.value.unshift(profile);
            successToast("Профиль создан", profile.name);
        }
        profileDialogVisible.value = false;
    } catch (error: any) {
        errorToast("Не удалось сохранить профиль", errorFmt(error));
    } finally {
        creatingProfile.value = false;
    }
}

async function launchRun(profile: DiscoveryProfile, dryRun = false): Promise<void> {
    launchingProfileId.value = profile.id;
    try {
        const run = await startDiscoveryRun(profile.id, dryRun);
        runs.value.unshift(run);
        activeTab.value = "runs";
        successToast("Discovery запущен", profile.name);
        updateRunPolling();
        await loadRuns(1);
    } catch (error: any) {
        errorToast("Не удалось запустить discovery", errorFmt(error));
    } finally {
        launchingProfileId.value = null;
    }
}

function confirmDeleteProfile(event: MouseEvent, profile: DiscoveryProfile): void {
    confirm.require({
        target: event.currentTarget as HTMLElement,
        message: `Удалить discovery profile "${profile.name}" и его историю запусков?`,
        icon: "pi pi-info-circle",
        acceptLabel: "Удалить",
        rejectLabel: "Отмена",
        acceptClass: "p-button-danger p-button-sm",
        defaultFocus: "reject",
        accept: () => deleteProfile(profile),
    });
}

async function deleteProfile(profile: DiscoveryProfile): Promise<void> {
    deletingProfileId.value = profile.id;
    try {
        await deleteDiscoveryProfile(profile.id);
        successToast("Профиль удален", profile.name);
        await Promise.all([loadProfiles(), loadRuns(1)]);
    } catch (error: any) {
        errorToast("Не удалось удалить профиль discovery", errorFmt(error));
    } finally {
        deletingProfileId.value = null;
    }
}

function confirmDeleteRun(event: MouseEvent, run: DiscoveryRun): void {
    confirm.require({
        target: event.currentTarget as HTMLElement,
        message: `Удалить запуск discovery #${run.id}?`,
        icon: "pi pi-info-circle",
        acceptLabel: "Удалить",
        rejectLabel: "Отмена",
        acceptClass: "p-button-danger p-button-sm",
        defaultFocus: "reject",
        accept: () => deleteRun(run),
    });
}

async function deleteRun(run: DiscoveryRun): Promise<void> {
    deletingRunId.value = run.id;
    try {
        await deleteDiscoveryRun(run.id);
        successToast("Запуск удален", getProfileName(run.profileId));
        const nextPage = runs.value.length === 1 && runsPage.value > 1 ? runsPage.value - 1 : runsPage.value;
        await loadRuns(nextPage);
    } catch (error: any) {
        errorToast("Не удалось удалить запуск discovery", errorFmt(error));
    } finally {
        deletingRunId.value = null;
    }
}

function confirmDeleteCandidate(event: MouseEvent, candidate: DiscoveryCandidate): void {
    confirm.require({
        target: event.currentTarget as HTMLElement,
        message: `Удалить кандидата ${candidate.name || candidate.ip}?`,
        icon: "pi pi-info-circle",
        acceptLabel: "Удалить",
        rejectLabel: "Отмена",
        acceptClass: "p-button-danger p-button-sm",
        defaultFocus: "reject",
        accept: () => deleteCandidate(candidate),
    });
}

async function deleteCandidate(candidate: DiscoveryCandidate): Promise<void> {
    deletingCandidateId.value = candidate.id;
    try {
        await deleteDiscoveryCandidate(candidate.id);
        successToast("Кандидат удален", candidate.name || candidate.ip);
        const nextPage = candidates.value.length === 1 && candidatesPage.value > 1 ? candidatesPage.value - 1 : candidatesPage.value;
        await loadCandidates(nextPage);
    } catch (error: any) {
        errorToast("Не удалось удалить кандидата discovery", errorFmt(error));
    } finally {
        deletingCandidateId.value = null;
    }
}

function openAcceptDialog(candidate: DiscoveryCandidate): void {
    selectedCandidate.value = candidate;
    acceptForm.name = candidate.name;
    acceptForm.deviceGroup = lookups.deviceGroups[0]?.id || null;
    acceptForm.authGroup = candidate.selectedAuthGroup || lookups.authGroups[0]?.id || null;
    acceptForm.cmdProtocol = "ssh";
    acceptForm.portScanProtocol = candidate.detectedProtocols.snmp ? "snmp" : "ssh";
    acceptForm.snmpCommunity = "";
    acceptForm.collectInterfaces = false;
    acceptDialogVisible.value = true;
}

async function acceptCandidate(): Promise<void> {
    if (!selectedCandidate.value) {
        return;
    }
    if (!acceptForm.deviceGroup || !acceptForm.authGroup) {
        errorToast("Не выбраны справочники", "Укажите группу оборудования и авторизацию.");
        return;
    }

    try {
        if (acceptForm.name.trim() && acceptForm.name.trim() !== selectedCandidate.value.name) {
            await patchDiscoveryCandidate(selectedCandidate.value.id, { name: acceptForm.name.trim() });
        }
        const result = await acceptDiscoveryCandidate(selectedCandidate.value.id, {
            deviceGroup: acceptForm.deviceGroup,
            authGroup: acceptForm.authGroup,
            cmdProtocol: acceptForm.cmdProtocol,
            portScanProtocol: acceptForm.portScanProtocol,
            snmpCommunity: acceptForm.snmpCommunity,
            collectInterfaces: acceptForm.collectInterfaces,
        });
        successToast("Устройство создано", result.deviceName);
        acceptDialogVisible.value = false;
        await loadCandidates(candidatesPage.value);
    } catch (error: any) {
        errorToast("Не удалось принять кандидата", errorFmt(error));
    }
}

async function ignoreCandidate(candidate: DiscoveryCandidate): Promise<void> {
    try {
        await ignoreDiscoveryCandidate(candidate.id);
        successToast("Кандидат скрыт", candidate.ip);
        await loadCandidates(candidatesPage.value);
    } catch (error: any) {
        errorToast("Не удалось изменить кандидата", errorFmt(error));
    }
}

function getStatusSeverity(status: string): "success" | "danger" | "warn" | "secondary" | "info" | "contrast" {
    switch (status) {
        case "SUCCESS":
        case "READY":
        case "CREATED":
            return "success";
        case "FAILURE":
        case "FAILED":
            return "danger";
        case "DUPLICATE":
        case "IGNORED":
        case "REVOKED":
            return "warn";
        case "PROGRESS":
        case "PENDING":
            return "info";
        default:
            return "secondary";
    }
}

function getRunProgress(run: DiscoveryRun): number {
    if (!run.total) {
        return 0;
    }
    return Math.round((run.processed / run.total) * 100);
}

function getProfileName(profileId: number): string {
    return profiles.value.find((profile) => profile.id === profileId)?.name || `#${profileId}`;
}

function getLookupName(items: DiscoveryLookupItem[], id: number | null): string {
    return items.find((item) => item.id === id)?.name || "—";
}

function updateRunPolling(): void {
    const hasActiveRuns = runs.value.some((run) => ["PENDING", "PROGRESS"].includes(run.status));
    if (hasActiveRuns && runPollingTimer == null) {
        runPollingTimer = window.setInterval(pollActiveRuns, 3000);
    }
    if (!hasActiveRuns && runPollingTimer != null) {
        clearInterval(runPollingTimer);
        runPollingTimer = null;
    }
}

async function pollActiveRuns(): Promise<void> {
    const activeRuns = runs.value.filter((run) => ["PENDING", "PROGRESS"].includes(run.status));
    if (!activeRuns.length) {
        updateRunPolling();
        return;
    }

    await Promise.all(
        activeRuns.map(async (run) => {
            try {
                const freshRun = await getDiscoveryRun(run.id);
                const index = runs.value.findIndex((item) => item.id === run.id);
                if (index >= 0) {
                    runs.value[index] = freshRun;
                }
            } catch (error: any) {
                console.error(error);
            }
        })
    );
    updateRunPolling();
}

function switchTab(tab: TabName): void {
    activeTab.value = tab;
    if (tab === "runs" && !runs.value.length) {
        loadRuns(1);
    }
    if (tab === "candidates" && !candidates.value.length) {
        loadCandidates(1);
    }
}

onMounted(async () => {
    await loadLookups();
    await Promise.all([loadProfiles(), loadRuns(1), loadCandidates(1)]);
});

onBeforeUnmount(() => {
    if (runPollingTimer != null) {
        clearInterval(runPollingTimer);
        runPollingTimer = null;
    }
});
</script>

<template>
    <Header />
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
                        <div class="rounded-2xl border border-gray-200/80 bg-gray-50/80 px-4 py-3 dark:border-gray-700/80 dark:bg-gray-800/60">
                            <div class="text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">Профили</div>
                            <div class="mt-1 text-2xl font-semibold text-gray-900 dark:text-gray-100">
                                {{ profiles.length }}
                            </div>
                        </div>
                        <div class="rounded-2xl border border-gray-200/80 bg-gray-50/80 px-4 py-3 dark:border-gray-700/80 dark:bg-gray-800/60">
                            <div class="text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">Активные</div>
                            <div class="mt-1 text-2xl font-semibold text-sky-700 dark:text-sky-200">
                                {{ activeRunsCount }}
                            </div>
                        </div>
                        <div class="rounded-2xl border border-gray-200/80 bg-gray-50/80 px-4 py-3 dark:border-gray-700/80 dark:bg-gray-800/60">
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
                <DataTable :value="profiles" :loading="loadingProfiles" dataKey="id" responsiveLayout="scroll">
                    <Column field="name" header="Профиль">
                        <template #body="{ data }">
                            <div class="font-semibold text-gray-900 dark:text-gray-100">{{ data.name }}</div>
                            <div class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                                {{ data.networks.join(", ") }}
                            </div>
                        </template>
                    </Column>
                    <Column header="Группа">
                        <template #body="{ data }">
                            {{ getLookupName(lookups.deviceGroups, data.deviceGroup) }}
                        </template>
                    </Column>
                    <Column header="Auth">
                        <template #body="{ data }">
                            <div class="flex flex-wrap gap-1">
                                <Badge
                                    v-for="authId in data.authGroups"
                                    :key="authId"
                                    severity="secondary"
                                    :value="getLookupName(lookups.authGroups, authId)"
                                />
                                <span v-if="!data.authGroups.length" class="text-sm text-gray-500">—</span>
                            </div>
                        </template>
                    </Column>
                    <Column header="Discovery">
                        <template #body="{ data }">
                            <div class="flex flex-wrap gap-1">
                                <Badge severity="info" :value="data.portScanProtocol" />
                                <Badge severity="secondary" :value="data.cmdProtocol" />
                                <Badge severity="contrast" :value="`${data.snmpCommunitiesCount} SNMP`" />
                            </div>
                        </template>
                    </Column>
                    <Column header="Авто">
                        <template #body="{ data }">
                            <Badge
                                :severity="data.autoCreate ? 'success' : 'secondary'"
                                :value="data.autoCreate ? `>= ${data.autoCreateMinConfidence}` : 'выкл'"
                            />
                        </template>
                    </Column>
                    <Column header="Действия">
                        <template #body="{ data }">
                            <div class="flex flex-wrap justify-end gap-2">
                                <Button
                                    icon="pi pi-pencil"
                                    label="Изменить"
                                    size="small"
                                    severity="secondary"
                                    outlined
                                    class="rounded-2xl!"
                                    @click="openEditProfileDialog(data)"
                                />
                                <Button
                                    icon="pi pi-play"
                                    label="Запуск"
                                    size="small"
                                    class="rounded-2xl!"
                                    :loading="launchingProfileId === data.id"
                                    @click="launchRun(data, false)"
                                />
                                <Button
                                    icon="pi pi-eye"
                                    label="Dry"
                                    size="small"
                                    severity="secondary"
                                    outlined
                                    class="rounded-2xl!"
                                    :loading="launchingProfileId === data.id"
                                    @click="launchRun(data, true)"
                                />
                                <Button
                                    icon="pi pi-trash"
                                    label="Удалить"
                                    size="small"
                                    severity="danger"
                                    outlined
                                    class="rounded-2xl!"
                                    :loading="deletingProfileId === data.id"
                                    @click="confirmDeleteProfile($event, data)"
                                />
                            </div>
                        </template>
                    </Column>
                </DataTable>

                <div v-if="!loadingProfiles && !profiles.length" class="py-10 text-center text-sm text-gray-500">
                    Профили discovery еще не созданы
                </div>
            </section>

            <section
                v-if="activeTab === 'runs'"
                class="rounded-3xl border border-gray-200/70 bg-white/80 p-4 backdrop-blur dark:border-gray-700/70 dark:bg-gray-900/45 sm:rounded-4xl sm:p-6"
            >
                <DataTable :value="runs" :loading="loadingRuns" dataKey="id" responsiveLayout="scroll">
                    <Column header="Запуск">
                        <template #body="{ data }">
                            <div class="font-semibold text-gray-900 dark:text-gray-100">
                                {{ getProfileName(data.profileId) }}
                            </div>
                            <div class="mt-1 font-mono text-xs text-gray-500">{{ data.task_id || `#${data.id}` }}</div>
                        </template>
                    </Column>
                    <Column header="Статус">
                        <template #body="{ data }">
                            <Badge :severity="getStatusSeverity(data.status)" :value="data.status" />
                        </template>
                    </Column>
                    <Column header="Прогресс">
                        <template #body="{ data }">
                            <div class="min-w-40">
                                <div class="h-2 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
                                    <div
                                        class="h-full rounded-full bg-sky-600 dark:bg-sky-400"
                                        :style="{ width: `${getRunProgress(data)}%` }"
                                    />
                                </div>
                                <div class="mt-1 text-xs text-gray-500">
                                    {{ data.processed }}/{{ data.total }} · {{ getRunProgress(data) }}%
                                </div>
                            </div>
                        </template>
                    </Column>
                    <Column header="Итоги">
                        <template #body="{ data }">
                            <div class="flex flex-wrap gap-1">
                                <Badge severity="success" :value="`found ${data.found}`" />
                                <Badge severity="info" :value="`created ${data.created}`" />
                                <Badge severity="warn" :value="`skip ${data.skipped}`" />
                                <Badge v-if="data.errors" severity="danger" :value="`err ${data.errors}`" />
                            </div>
                        </template>
                    </Column>
                    <Column header="Время">
                        <template #body="{ data }">
                            <div class="text-sm text-gray-700 dark:text-gray-200">
                                {{ verboseDatetime(data.created_at) }}
                            </div>
                            <div class="text-xs text-gray-500">
                                {{ data.finished_at ? verboseDatetime(data.finished_at) : "в процессе" }}
                            </div>
                        </template>
                    </Column>
                    <Column header="Действия">
                        <template #body="{ data }">
                            <div class="flex justify-end">
                                <Button
                                    icon="pi pi-trash"
                                    label="Удалить"
                                    size="small"
                                    severity="danger"
                                    outlined
                                    class="rounded-2xl!"
                                    :loading="deletingRunId === data.id"
                                    @click="confirmDeleteRun($event, data)"
                                />
                            </div>
                        </template>
                    </Column>
                </DataTable>

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
                <div class="mb-5 grid gap-3 lg:grid-cols-[1fr,16rem,16rem,auto]">
                    <IconField>
                        <InputIcon class="pi pi-search" />
                        <InputText
                            v-model.trim="candidateSearch"
                            fluid
                            placeholder="IP, имя или hostname"
                            class="rounded-2xl"
                            @keyup.enter="loadCandidates(1)"
                        />
                    </IconField>
                    <Select
                        v-model="candidateStatus"
                        :options="statusOptions"
                        optionLabel="label"
                        optionValue="value"
                        class="w-full rounded-2xl"
                        @change="loadCandidates(1)"
                    />
                    <Select
                        v-model="candidateVendor"
                        :options="[{ label: 'Все вендоры', value: '' }, ...candidateVendors]"
                        optionLabel="label"
                        optionValue="value"
                        class="w-full rounded-2xl"
                        @change="loadCandidates(1)"
                    />
                    <Button
                        icon="pi pi-search"
                        label="Найти"
                        class="rounded-2xl!"
                        :loading="loadingCandidates"
                        @click="loadCandidates(1)"
                    />
                </div>

                <DataTable :value="candidates" :loading="loadingCandidates" dataKey="id" responsiveLayout="scroll">
                    <Column header="Кандидат">
                        <template #body="{ data }">
                            <div class="font-semibold text-gray-900 dark:text-gray-100">{{ data.name || data.ip }}</div>
                            <div class="mt-1 font-mono text-xs text-gray-500">{{ data.ip }}</div>
                        </template>
                    </Column>
                    <Column header="Identity">
                        <template #body="{ data }">
                            <div class="text-sm text-gray-800 dark:text-gray-200">
                                {{ [data.vendor, data.model].filter(Boolean).join(" · ") || "—" }}
                            </div>
                            <div class="mt-1 max-w-90 truncate text-xs text-gray-500">
                                {{ data.serialNumber || data.sysName || data.sysDescr || "без fingerprint" }}
                            </div>
                        </template>
                    </Column>
                    <Column header="Статус">
                        <template #body="{ data }">
                            <div class="flex flex-col gap-1">
                                <Badge :severity="getStatusSeverity(data.status)" :value="data.status" />
                                <span class="text-xs text-gray-500">confidence {{ data.confidence }}</span>
                            </div>
                        </template>
                    </Column>
                    <Column header="Протоколы">
                        <template #body="{ data }">
                            <div class="flex flex-wrap gap-1">
                                <Badge
                                    v-for="(enabled, protocol) in data.detectedProtocols"
                                    :key="protocol"
                                    :severity="enabled ? 'success' : 'secondary'"
                                    :value="protocol"
                                />
                            </div>
                        </template>
                    </Column>
                    <Column header="Последний раз">
                        <template #body="{ data }">
                            <div class="text-sm text-gray-700 dark:text-gray-200">
                                {{ verboseDatetime(data.last_seen_at) }}
                            </div>
                            <div v-if="data.lastError" class="mt-1 max-w-80 truncate text-xs text-rose-600">
                                {{ data.lastError }}
                            </div>
                        </template>
                    </Column>
                    <Column header="Действия">
                        <template #body="{ data }">
                            <div class="flex flex-wrap justify-end gap-2">
                                <Button
                                    v-if="data.status === 'READY' || data.status === 'NEW'"
                                    icon="pi pi-check"
                                    label="Принять"
                                    size="small"
                                    class="rounded-2xl!"
                                    @click="openAcceptDialog(data)"
                                />
                                <Button
                                    v-if="data.status !== 'IGNORED' && data.status !== 'CREATED'"
                                    icon="pi pi-eye-slash"
                                    label="Игнор"
                                    size="small"
                                    severity="secondary"
                                    outlined
                                    class="rounded-2xl!"
                                    @click="ignoreCandidate(data)"
                                />
                                <Button
                                    icon="pi pi-trash"
                                    label="Удалить"
                                    size="small"
                                    severity="danger"
                                    outlined
                                    class="rounded-2xl!"
                                    :loading="deletingCandidateId === data.id"
                                    @click="confirmDeleteCandidate($event, data)"
                                />
                            </div>
                        </template>
                    </Column>
                </DataTable>

                <div v-if="!loadingCandidates && !candidates.length" class="py-10 text-center text-sm text-gray-500">
                    По текущим фильтрам кандидаты не найдены
                </div>

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

    <Dialog
        v-model:visible="profileDialogVisible"
        modal
        maximizable
        :header="editingProfile ? 'Изменить discovery profile' : 'Новый discovery profile'"
        class="w-[min(96vw,980px)]"
    >
        <div class="grid gap-4 lg:grid-cols-2">
            <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                Имя
                <InputText v-model.trim="profileForm.name" class="rounded-2xl" />
            </label>
            <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                Группа оборудования
                <Select
                    v-model="profileForm.deviceGroup"
                    :options="lookups.deviceGroups"
                    optionLabel="name"
                    optionValue="id"
                    class="rounded-2xl"
                />
            </label>
            <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                Подсети
                <Textarea v-model="profileForm.networks" rows="4" class="rounded-2xl" />
            </label>
            <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                Исключения
                <Textarea v-model="profileForm.excludeIps" rows="4" class="rounded-2xl" />
            </label>
            <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                SNMP community
                <Textarea v-model="profileForm.snmpCommunities" rows="4" class="rounded-2xl" />
                <span v-if="editingProfile" class="text-xs font-normal text-gray-500">
                    Оставьте пустым, чтобы не менять сохраненные community.
                </span>
            </label>
            <div class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                Auth groups
                <div class="grid max-h-34 gap-2 overflow-auto rounded-2xl border border-gray-200/80 p-3 dark:border-gray-700/80">
                    <label
                        v-for="authGroup in lookups.authGroups"
                        :key="authGroup.id"
                        class="flex cursor-pointer items-center gap-2 text-sm font-normal"
                    >
                        <Checkbox v-model="profileForm.authGroups" :value="authGroup.id" />
                        <span>{{ authGroup.name }}</span>
                    </label>
                </div>
            </div>
            <div class="grid gap-4 sm:grid-cols-2">
                <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                    Port scan
                    <Select
                        v-model="profileForm.portScanProtocol"
                        :options="portScanProtocolOptions"
                        optionLabel="label"
                        optionValue="value"
                        class="rounded-2xl"
                    />
                </label>
                <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                    Command
                    <Select
                        v-model="profileForm.cmdProtocol"
                        :options="cmdProtocolOptions"
                        optionLabel="label"
                        optionValue="value"
                        class="rounded-2xl"
                    />
                </label>
            </div>
            <div class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                CLI protocols
                <div class="flex flex-wrap gap-3 rounded-2xl border border-gray-200/80 p-3 dark:border-gray-700/80">
                    <label
                        v-for="protocol in protocolOptions"
                        :key="protocol.value"
                        class="flex cursor-pointer items-center gap-2 text-sm font-normal"
                    >
                        <Checkbox v-model="profileForm.tryProtocols" :value="protocol.value" />
                        <span>{{ protocol.label }}</span>
                    </label>
                </div>
            </div>
            <div class="grid gap-4 sm:grid-cols-3">
                <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                    Workers
                    <input
                        v-model.number="profileForm.maxWorkers"
                        type="number"
                        min="1"
                        max="80"
                        class="rounded-2xl border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100"
                    />
                </label>
                <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                    Timeout
                    <input
                        v-model.number="profileForm.timeoutSeconds"
                        type="number"
                        min="1"
                        max="30"
                        class="rounded-2xl border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100"
                    />
                </label>
                <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                    Confidence
                    <input
                        v-model.number="profileForm.autoCreateMinConfidence"
                        type="number"
                        min="0"
                        max="100"
                        class="rounded-2xl border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100"
                    />
                </label>
            </div>
            <div class="flex flex-wrap items-center gap-6 rounded-2xl border border-gray-200/80 p-3 dark:border-gray-700/80">
                <label class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                    <ToggleSwitch v-model="profileForm.autoCreate" />
                    Автосоздание
                </label>
                <label class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                    <ToggleSwitch v-model="profileForm.isActive" />
                    Активен
                </label>
            </div>
        </div>

        <div class="mt-6 flex justify-end gap-2">
            <Button
                label="Отмена"
                icon="pi pi-times"
                severity="secondary"
                outlined
                class="rounded-2xl!"
                @click="profileDialogVisible = false"
            />
            <Button
                :label="editingProfile ? 'Сохранить' : 'Создать'"
                icon="pi pi-check"
                class="rounded-2xl!"
                :loading="creatingProfile"
                @click="saveProfile"
            />
        </div>
    </Dialog>

    <Dialog
        v-model:visible="acceptDialogVisible"
        modal
        maximizable
        header="Принять кандидата"
        class="w-[min(96vw,720px)]"
    >
        <div v-if="selectedCandidate" class="grid gap-4">
            <div class="rounded-2xl border border-gray-200/80 bg-gray-50/80 p-4 dark:border-gray-700/80 dark:bg-gray-800/60">
                <div class="font-mono text-sm text-gray-500">{{ selectedCandidate.ip }}</div>
                <div class="mt-1 text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {{ [selectedCandidate.vendor, selectedCandidate.model].filter(Boolean).join(" · ") || "Unknown" }}
                </div>
            </div>
            <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                Имя устройства
                <InputText v-model.trim="acceptForm.name" class="rounded-2xl" />
            </label>
            <div class="grid gap-4 sm:grid-cols-2">
                <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                    Группа оборудования
                    <Select
                        v-model="acceptForm.deviceGroup"
                        :options="lookups.deviceGroups"
                        optionLabel="name"
                        optionValue="id"
                        class="rounded-2xl"
                    />
                </label>
                <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                    Auth group
                    <Select
                        v-model="acceptForm.authGroup"
                        :options="lookups.authGroups"
                        optionLabel="name"
                        optionValue="id"
                        class="rounded-2xl"
                    />
                </label>
            </div>
            <div class="grid gap-4 sm:grid-cols-3">
                <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                    Port scan
                    <Select
                        v-model="acceptForm.portScanProtocol"
                        :options="portScanProtocolOptions"
                        optionLabel="label"
                        optionValue="value"
                        class="rounded-2xl"
                    />
                </label>
                <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                    Command
                    <Select
                        v-model="acceptForm.cmdProtocol"
                        :options="cmdProtocolOptions"
                        optionLabel="label"
                        optionValue="value"
                        class="rounded-2xl"
                    />
                </label>
                <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                    SNMP community
                    <InputText v-model.trim="acceptForm.snmpCommunity" class="rounded-2xl" />
                </label>
            </div>
            <label class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                <ToggleSwitch v-model="acceptForm.collectInterfaces" />
                Первичный сбор интерфейсов
            </label>
        </div>

        <div class="mt-6 flex justify-end gap-2">
            <Button
                label="Отмена"
                icon="pi pi-times"
                severity="secondary"
                outlined
                class="rounded-2xl!"
                @click="acceptDialogVisible = false"
            />
            <Button label="Создать устройство" icon="pi pi-check" class="rounded-2xl!" @click="acceptCandidate" />
        </div>
    </Dialog>

    <Footer />
</template>
