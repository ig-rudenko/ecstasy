import api from "@/services/api";
import type {
    GatheringResultFilters,
    GatheringResultLookups,
    GatheringResultsPage,
    GatheringTimelineResponse,
} from "@/types/gatheringResults";

function setDate(params: URLSearchParams, name: string, value: Date | null): void {
    if (value) params.set(name, value.toISOString());
}

function buildQuery(filters: GatheringResultFilters): URLSearchParams {
    const params = new URLSearchParams();
    if (filters.deviceGroup) params.set("device_group", String(filters.deviceGroup));
    if (filters.deviceName.trim()) params.set("device_name", filters.deviceName.trim());
    if (filters.vendor) params.set("vendor", filters.vendor);
    if (filters.model) params.set("model", filters.model);
    if (filters.taskStatus) params.set("task_status", filters.taskStatus);
    if (filters.taskName) params.set("task_name", filters.taskName);
    setDate(params, "task_started_after", filters.taskStartedAfter);
    setDate(params, "task_started_before", filters.taskStartedBefore);
    if (filters.resultStatus) params.set("result_status", filters.resultStatus);
    setDate(params, "result_started_after", filters.resultStartedAfter);
    setDate(params, "result_started_before", filters.resultStartedBefore);
    if (filters.errorType) params.set("error_type", filters.errorType);
    if (filters.errorMessage.trim()) params.set("error_message", filters.errorMessage.trim());
    return params;
}

export async function getGatheringResults(
    filters: GatheringResultFilters,
    page: number,
    pageSize: number
): Promise<GatheringResultsPage> {
    const params = buildQuery(filters);
    params.set("page", String(page));
    params.set("page_size", String(pageSize));
    const response = await api.get<GatheringResultsPage>(`/api/v1/gather/task-results/?${params}`);
    return response.data;
}

export async function getGatheringTimeline(
    filters: GatheringResultFilters,
    taskName: string | null
): Promise<GatheringTimelineResponse> {
    const timelineFilters = { ...filters, taskName };
    const params = buildQuery(timelineFilters);
    const response = await api.get<GatheringTimelineResponse>(`/api/v1/gather/task-results/timeline/?${params}`);
    return response.data;
}

export async function getGatheringResultLookups(): Promise<GatheringResultLookups> {
    const response = await api.get<GatheringResultLookups>("/api/v1/gather/task-results/lookups/");
    return response.data;
}
