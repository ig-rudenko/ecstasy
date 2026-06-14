import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { useConfirm } from "primevue/useconfirm";
import errorFmt from "@/errorFmt";
import { errorToast, successToast } from "@/services/my.toast";
import {
    acceptDiscoveryCandidate,
    AcceptCandidatePayload,
    bulkDeleteDiscoveryCandidates,
    createDiscoveryProfile,
    deleteDiscoveryCandidate,
    deleteDiscoveryProfile,
    deleteDiscoveryRun,
    DiscoveryCandidate,
    DiscoveryCandidateTableQuery,
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
    rescanDiscoveryCandidates,
    startDiscoveryRun,
} from "@/services/discovery";

type TabName = "profiles" | "runs" | "candidates";

export function useDiscoveryPage() {
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
    const selectedCandidateIds = ref<number[]>([]);
    const candidateStatus = ref("");
    const candidateSearch = ref("");
    const candidateVendor = ref("");
    const candidateTableQuery = reactive<DiscoveryCandidateTableQuery>({
        name: "",
        ip: "",
        authCheckStatus: "",
        confidenceMin: null,
        confidenceMax: null,
        protocols: [],
        model: "",
        osVersion: "",
        lastError: "",
        authCheckError: "",
        ordering: "",
    });
    const loadingProfiles = ref(false);
    const loadingRuns = ref(false);
    const loadingCandidates = ref(false);
    const creatingProfile = ref(false);
    const launchingProfileId = ref<number | null>(null);
    const deletingProfileId = ref<number | null>(null);
    const deletingRunId = ref<number | null>(null);
    const deletingCandidateId = ref<number | null>(null);
    const rescanningCandidateId = ref<number | null>(null);
    const rescanningSelected = ref(false);
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
        portScanProtocol: "snmp" as "auto" | "snmp" | "telnet" | "ssh",
        cmdProtocol: "ssh" as "auto" | "telnet" | "ssh",
        maxWorkers: 32,
        timeoutSeconds: 2,
        autoCreate: false,
        autoCreateMinConfidence: 70,
        activateCreatedDevices: false,
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
    const protocolOptions: { label: string; value: "ssh" | "telnet" }[] = [
        { label: "SSH", value: "ssh" },
        { label: "Telnet", value: "telnet" },
    ];
    const portScanProtocolOptions: { label: string; value: "snmp" | "ssh" | "telnet" }[] = [
        { label: "SNMP", value: "snmp" },
        { label: "SSH", value: "ssh" },
        { label: "Telnet", value: "telnet" },
    ];
    const cmdProtocolOptions: { label: string; value: "ssh" | "telnet" }[] = [
        { label: "SSH", value: "ssh" },
        { label: "Telnet", value: "telnet" },
    ];
    const profilePortScanProtocolOptions: {
        label: string;
        value: "auto" | "snmp" | "ssh" | "telnet";
    }[] = [{ label: "Авто: SSH → Telnet", value: "auto" }, ...portScanProtocolOptions];
    const profileCmdProtocolOptions: {
        label: string;
        value: "auto" | "ssh" | "telnet";
    }[] = [{ label: "Авто: SSH → Telnet", value: "auto" }, ...cmdProtocolOptions];

    const readyCandidatesCount = computed(
        () => candidates.value.filter((candidate) => candidate.status === "READY").length
    );
    const activeRunsCount = computed(
        () => runs.value.filter((run) => ["PENDING", "PROGRESS"].includes(run.status)).length
    );
    const candidateVendors = computed(() => {
        const vendors = new Set(candidates.value.map((candidate) => candidate.vendor).filter(Boolean));
        return [...vendors]
            .sort((left, right) => left.localeCompare(right))
            .map((vendor) => ({ label: vendor, value: vendor }));
    });
    const candidateVendorOptions = computed(() => [{ label: "Все вендоры", value: "" }, ...candidateVendors.value]);

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
        profileForm.activateCreatedDevices = false;
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
        profileForm.activateCreatedDevices = profile.activateCreatedDevices;
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
            activateCreatedDevices: profileForm.activateCreatedDevices,
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
                ...candidateTableQuery,
            });
            candidates.value = response.results;
            candidatesTotal.value = response.count;
            candidatesPage.value = page;
            selectedCandidateIds.value = selectedCandidateIds.value.filter((id) =>
                response.results.some((candidate) => candidate.id === id)
            );
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

    function getProfileName(profileId: number): string {
        return profiles.value.find((profile) => profile.id === profileId)?.name || `#${profileId}`;
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

    async function deleteCandidate(candidate: DiscoveryCandidate): Promise<void> {
        deletingCandidateId.value = candidate.id;
        try {
            await deleteDiscoveryCandidate(candidate.id);
            successToast("Кандидат удален", candidate.name || candidate.ip);
            const nextPage =
                candidates.value.length === 1 && candidatesPage.value > 1
                    ? candidatesPage.value - 1
                    : candidatesPage.value;
            await loadCandidates(nextPage);
        } catch (error: any) {
            errorToast("Не удалось удалить кандидата discovery", errorFmt(error));
        } finally {
            deletingCandidateId.value = null;
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

    async function rescanCandidates(candidateIds: number[]): Promise<void> {
        const result = await rescanDiscoveryCandidates(candidateIds);
        if (result.runs.length) {
            runs.value = [
                ...result.runs,
                ...runs.value.filter((run) => !result.runs.some((createdRun) => createdRun.id === run.id)),
            ];
            successToast("Переопрос запущен", `Запусков: ${result.runs.length}`);
            updateRunPolling();
        }
        if (result.skipped.length) {
            errorToast(
                "Часть кандидатов не запущена",
                result.skipped.map((item) => `${item.ip || `#${item.id}`}: ${item.reason}`).join("\n")
            );
        }
    }

    async function rescanCandidate(candidate: DiscoveryCandidate): Promise<void> {
        rescanningCandidateId.value = candidate.id;
        try {
            await rescanCandidates([candidate.id]);
        } catch (error: any) {
            errorToast("Не удалось переопросить кандидата", errorFmt(error));
        } finally {
            rescanningCandidateId.value = null;
        }
    }

    function confirmRescanCandidate(event: MouseEvent, candidate: DiscoveryCandidate): void {
        confirm.require({
            target: event.currentTarget as HTMLElement,
            message: `Переопросить кандидата ${candidate.name || candidate.ip}?`,
            icon: "pi pi-info-circle",
            acceptLabel: "Переопросить",
            rejectLabel: "Отмена",
            acceptClass: "p-button-sm",
            defaultFocus: "reject",
            accept: () => rescanCandidate(candidate),
        });
    }

    function resolveCandidateCmdProtocol(candidate: DiscoveryCandidate): "ssh" | "telnet" {
        const protocol = (candidate.rawFingerprint?.cliProtocol as string) || "";
        if (protocol === "ssh" || protocol === "telnet") {
            return protocol;
        }
        if (candidate.detectedProtocols.ssh) {
            return "ssh";
        }
        if (candidate.detectedProtocols.telnet) {
            return "telnet";
        }
        return "ssh";
    }

    function resolveCandidatePortScanProtocol(candidate: DiscoveryCandidate): "snmp" | "ssh" | "telnet" {
        const cliProtocol = candidate.rawFingerprint?.cliProtocol;
        if (cliProtocol === "ssh" || cliProtocol === "telnet") {
            return cliProtocol;
        }
        if (candidate.detectedProtocols.snmp) {
            return "snmp";
        }
        return resolveCandidateCmdProtocol(candidate);
    }

    function openAcceptDialog(candidate: DiscoveryCandidate): void {
        selectedCandidate.value = candidate;
        acceptForm.name = candidate.name;
        acceptForm.deviceGroup = lookups.deviceGroups[0]?.id || null;
        acceptForm.authGroup = candidate.selectedAuthGroup;
        acceptForm.cmdProtocol = resolveCandidateCmdProtocol(candidate);
        acceptForm.portScanProtocol = resolveCandidatePortScanProtocol(candidate);
        acceptForm.snmpCommunity = "";
        acceptForm.collectInterfaces = false;
        acceptDialogVisible.value = true;
    }

    function buildAcceptPayload(candidate: DiscoveryCandidate): AcceptCandidatePayload | null {
        const deviceGroup = lookups.deviceGroups[0]?.id || null;
        const authGroup = candidate.selectedAuthGroup;
        if (!deviceGroup || !authGroup) {
            return null;
        }
        return {
            deviceGroup,
            authGroup,
            cmdProtocol: resolveCandidateCmdProtocol(candidate),
            portScanProtocol: resolveCandidatePortScanProtocol(candidate),
            snmpCommunity: "",
            collectInterfaces: false,
        };
    }

    async function acceptCandidate(): Promise<void> {
        if (!selectedCandidate.value) return;
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

    async function quickAcceptCandidate(candidate: DiscoveryCandidate): Promise<void> {
        try {
            const payload = buildAcceptPayload(candidate);
            if (!payload) {
                errorToast(
                    "Нет проверенной AuthGroup",
                    "Быстрое добавление доступно только после успешной проверки AuthGroup."
                );
                return;
            }
            const result = await acceptDiscoveryCandidate(candidate.id, payload);
            successToast("Устройство создано", result.deviceName);
            await loadCandidates(candidatesPage.value);
        } catch (error: any) {
            errorToast("Не удалось быстро добавить кандидата", errorFmt(error));
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

    function getSelectedCandidates(): DiscoveryCandidate[] {
        return candidates.value.filter((candidate) => selectedCandidateIds.value.includes(candidate.id));
    }
    function setSelectedCandidateIds(value: number[]): void {
        selectedCandidateIds.value = value;
    }
    function setCandidateSearch(value: string): void {
        candidateSearch.value = value.trim();
    }
    function setCandidateStatus(value: string): void {
        candidateStatus.value = value;
    }
    function setCandidateVendor(value: string): void {
        candidateVendor.value = value;
    }
    async function setCandidateTableQuery(value: DiscoveryCandidateTableQuery): Promise<void> {
        Object.assign(candidateTableQuery, value);
        await loadCandidates(1);
    }

    async function deleteSelectedCandidates(): Promise<void> {
        const selected = getSelectedCandidates();
        if (!selected.length) return;
        try {
            const result = await bulkDeleteDiscoveryCandidates(selected.map((candidate) => candidate.id));
            successToast("Кандидаты удалены", `Удалено: ${result.deleted}`);
            const nextPage =
                selected.length === candidates.value.length && candidatesPage.value > 1
                    ? candidatesPage.value - 1
                    : candidatesPage.value;
            await loadCandidates(nextPage);
        } catch (error: any) {
            errorToast("Не удалось удалить выбранных кандидатов", errorFmt(error));
        }
    }

    function confirmDeleteSelectedCandidates(event: MouseEvent): void {
        const selected = getSelectedCandidates();
        if (!selected.length) return;
        confirm.require({
            target: event.currentTarget as HTMLElement,
            message: `Удалить выбранных кандидатов: ${selected.length} шт.?`,
            icon: "pi pi-info-circle",
            acceptLabel: "Удалить",
            rejectLabel: "Отмена",
            acceptClass: "p-button-danger p-button-sm",
            defaultFocus: "reject",
            accept: () => deleteSelectedCandidates(),
        });
    }

    async function rescanSelectedCandidates(): Promise<void> {
        const selected = getSelectedCandidates();
        if (!selected.length) return;
        rescanningSelected.value = true;
        try {
            await rescanCandidates(selected.map((candidate) => candidate.id));
        } catch (error: any) {
            errorToast("Не удалось переопросить выбранных кандидатов", errorFmt(error));
        } finally {
            rescanningSelected.value = false;
        }
    }

    function confirmRescanSelectedCandidates(event: MouseEvent): void {
        const selected = getSelectedCandidates();
        if (!selected.length) return;
        confirm.require({
            target: event.currentTarget as HTMLElement,
            message: `Переопросить выбранных кандидатов: ${selected.length} шт.?`,
            icon: "pi pi-info-circle",
            acceptLabel: "Переопросить",
            rejectLabel: "Отмена",
            acceptClass: "p-button-sm",
            defaultFocus: "reject",
            accept: () => rescanSelectedCandidates(),
        });
    }

    async function quickAcceptSelectedCandidates(): Promise<void> {
        const selected = getSelectedCandidates().filter(
            (candidate) => candidate.status === "READY" || candidate.status === "NEW"
        );
        if (!selected.length) {
            errorToast("Нет кандидатов для добавления", "Выберите кандидатов со статусом READY или NEW.");
            return;
        }
        let successCount = 0;
        for (const candidate of selected) {
            const payload = buildAcceptPayload(candidate);
            if (!payload) continue;
            try {
                await acceptDiscoveryCandidate(candidate.id, payload);
                successCount += 1;
            } catch {
                // Частичные ошибки не прерывают пакетное добавление.
            }
        }
        if (successCount > 0) {
            successToast("Пакетное добавление завершено", `Добавлено: ${successCount}`);
        } else {
            errorToast(
                "Не удалось добавить выбранных кандидатов",
                "Проверьте доступность auth group и статусы кандидатов."
            );
        }
        await loadCandidates(candidatesPage.value);
    }

    function confirmQuickAcceptSelectedCandidates(event: MouseEvent): void {
        const selected = getSelectedCandidates().filter(
            (candidate) => candidate.status === "READY" || candidate.status === "NEW"
        );
        if (!selected.length) {
            errorToast("Нет кандидатов для добавления", "Выберите кандидатов со статусом READY или NEW.");
            return;
        }
        confirm.require({
            target: event.currentTarget as HTMLElement,
            message: `Быстро добавить выбранных кандидатов: ${selected.length} шт.?`,
            icon: "pi pi-info-circle",
            acceptLabel: "Добавить",
            rejectLabel: "Отмена",
            acceptClass: "p-button-sm",
            defaultFocus: "reject",
            accept: () => quickAcceptSelectedCandidates(),
        });
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
                    if (index >= 0) runs.value[index] = freshRun;
                } catch (error: any) {
                    console.error(error);
                }
            })
        );
        if (!runs.value.some((run) => ["PENDING", "PROGRESS"].includes(run.status))) {
            await loadCandidates(candidatesPage.value);
        }
        updateRunPolling();
    }

    function updateRunPolling(): void {
        const hasActiveRuns = runs.value.some((run) => ["PENDING", "PROGRESS"].includes(run.status));
        if (hasActiveRuns && runPollingTimer == null) runPollingTimer = window.setInterval(pollActiveRuns, 3000);
        if (!hasActiveRuns && runPollingTimer != null) {
            clearInterval(runPollingTimer);
            runPollingTimer = null;
        }
    }

    function switchTab(tab: TabName): void {
        activeTab.value = tab;
        if (tab === "runs" && !runs.value.length) loadRuns(1);
        if (tab === "candidates" && !candidates.value.length) loadCandidates(1);
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

    return {
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
        candidateTableQuery,
        loadingProfiles,
        loadingRuns,
        loadingCandidates,
        creatingProfile,
        launchingProfileId,
        deletingProfileId,
        deletingRunId,
        deletingCandidateId,
        rescanningCandidateId,
        rescanningSelected,
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
        profilePortScanProtocolOptions,
        profileCmdProtocolOptions,
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
        confirmRescanCandidate,
        openAcceptDialog,
        quickAcceptCandidate,
        ignoreCandidate,
        setSelectedCandidateIds,
        setCandidateSearch,
        setCandidateStatus,
        setCandidateVendor,
        setCandidateTableQuery,
        confirmDeleteSelectedCandidates,
        confirmRescanSelectedCandidates,
        confirmQuickAcceptSelectedCandidates,
        acceptCandidate,
        switchTab,
    };
}
