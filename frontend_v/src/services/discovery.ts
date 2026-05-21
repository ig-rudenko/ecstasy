import api from "@/services/api";

export interface DiscoveryLookupItem {
    id: number;
    name: string;
    description: string | null;
}

export interface DiscoveryLookups {
    deviceGroups: DiscoveryLookupItem[];
    authGroups: DiscoveryLookupItem[];
}

export interface DiscoveryProfile {
    id: number;
    name: string;
    networks: string[];
    exclude_ips: string[];
    deviceGroup: number;
    authGroups: number[];
    snmpCommunitiesCount: number;
    tryProtocols: string[];
    portScanProtocol: "snmp" | "telnet" | "ssh";
    cmdProtocol: "telnet" | "ssh";
    maxWorkers: number;
    timeoutSeconds: number;
    autoCreate: boolean;
    autoCreateMinConfidence: number;
    isActive: boolean;
    created_at: string;
    updated_at: string;
}

export interface DiscoveryProfilePayload {
    name: string;
    networks: string[];
    exclude_ips: string[];
    deviceGroup: number | null;
    authGroups: number[];
    snmpCommunities?: string[];
    tryProtocols: string[];
    portScanProtocol: "snmp" | "telnet" | "ssh";
    cmdProtocol: "telnet" | "ssh";
    maxWorkers: number;
    timeoutSeconds: number;
    autoCreate: boolean;
    autoCreateMinConfidence: number;
    isActive: boolean;
}

export interface DiscoveryRun {
    id: number;
    profileId: number;
    task_id: string;
    status: string;
    total: number;
    processed: number;
    found: number;
    created: number;
    skipped: number;
    errors: number;
    dry_run: boolean;
    summary: Record<string, unknown>;
    createdBy: string | null;
    started_at: string | null;
    finished_at: string | null;
    created_at: string;
}

export interface DiscoveryCandidate {
    id: number;
    ip: string;
    name: string;
    vendor: string;
    model: string;
    serialNumber: string;
    osVersion: string;
    macAddress: string;
    sysName: string;
    sysDescr: string;
    sysObjectId: string;
    source: string;
    status: string;
    confidence: number;
    detectedProtocols: Record<string, boolean>;
    selectedAuthGroup: number | null;
    selectedSnmpCommunitySet: boolean;
    deviceId: number | null;
    rawFingerprint: Record<string, unknown>;
    lastError: string;
    first_seen_at: string;
    last_seen_at: string;
}

export interface PaginatedResponse<T> {
    count: number;
    next: string | null;
    previous: string | null;
    results: T[];
}

export interface AcceptCandidatePayload {
    deviceGroup: number | null;
    authGroup: number | null;
    cmdProtocol: "telnet" | "ssh";
    portScanProtocol: "snmp" | "telnet" | "ssh";
    snmpCommunity: string;
    collectInterfaces: boolean;
}

export async function getDiscoveryLookups(): Promise<DiscoveryLookups> {
    const response = await api.get<DiscoveryLookups>("/api/v1/discovery/lookups");
    return response.data;
}

export async function getDiscoveryProfiles(): Promise<DiscoveryProfile[]> {
    const response = await api.get<PaginatedResponse<DiscoveryProfile> | DiscoveryProfile[]>(
        "/api/v1/discovery/profiles"
    );
    return Array.isArray(response.data) ? response.data : response.data.results;
}

export async function createDiscoveryProfile(payload: DiscoveryProfilePayload): Promise<DiscoveryProfile> {
    const response = await api.post<DiscoveryProfile>("/api/v1/discovery/profiles", payload);
    return response.data;
}

export async function patchDiscoveryProfile(
    profileId: number,
    payload: Partial<DiscoveryProfilePayload>
): Promise<DiscoveryProfile> {
    const response = await api.patch<DiscoveryProfile>(`/api/v1/discovery/profiles/${profileId}`, payload);
    return response.data;
}

export async function deleteDiscoveryProfile(profileId: number): Promise<void> {
    await api.delete(`/api/v1/discovery/profiles/${profileId}`);
}

export async function startDiscoveryRun(profileId: number, dryRun: boolean): Promise<DiscoveryRun> {
    const response = await api.post<DiscoveryRun>("/api/v1/discovery/runs", { profileId, dryRun });
    return response.data;
}

export async function getDiscoveryRuns(page = 1): Promise<PaginatedResponse<DiscoveryRun>> {
    const response = await api.get<PaginatedResponse<DiscoveryRun>>(`/api/v1/discovery/runs?page=${page}`);
    return response.data;
}

export async function getDiscoveryRun(runId: number): Promise<DiscoveryRun> {
    const response = await api.get<DiscoveryRun>(`/api/v1/discovery/runs/${runId}`);
    return response.data;
}

export async function deleteDiscoveryRun(runId: number): Promise<void> {
    await api.delete(`/api/v1/discovery/runs/${runId}`);
}

export async function getDiscoveryCandidates(params: {
    page?: number;
    status?: string;
    search?: string;
    vendor?: string;
}): Promise<PaginatedResponse<DiscoveryCandidate>> {
    const searchParams = new URLSearchParams();
    if (params.page) searchParams.set("page", String(params.page));
    if (params.status) searchParams.set("status", params.status);
    if (params.search?.trim()) searchParams.set("search", params.search.trim());
    if (params.vendor?.trim()) searchParams.set("vendor", params.vendor.trim());

    const response = await api.get<PaginatedResponse<DiscoveryCandidate>>(
        `/api/v1/discovery/candidates?${searchParams.toString()}`
    );
    return response.data;
}

export async function patchDiscoveryCandidate(
    candidateId: number,
    payload: Partial<DiscoveryCandidate>
): Promise<DiscoveryCandidate> {
    const response = await api.patch<DiscoveryCandidate>(`/api/v1/discovery/candidates/${candidateId}`, payload);
    return response.data;
}

export async function deleteDiscoveryCandidate(candidateId: number): Promise<void> {
    await api.delete(`/api/v1/discovery/candidates/${candidateId}`);
}

export async function acceptDiscoveryCandidate(
    candidateId: number,
    payload: AcceptCandidatePayload
): Promise<{ deviceId: number; deviceName: string }> {
    const response = await api.post<{ deviceId: number; deviceName: string }>(
        `/api/v1/discovery/candidates/${candidateId}/accept`,
        payload
    );
    return response.data;
}

export async function ignoreDiscoveryCandidate(candidateId: number): Promise<DiscoveryCandidate> {
    const response = await api.post<DiscoveryCandidate>(`/api/v1/discovery/candidates/${candidateId}/ignore`);
    return response.data;
}
