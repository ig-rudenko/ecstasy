import type { PaginatedResponse } from "@/types/paginator";

export type GatheringTaskStatus = "RUNNING" | "SUCCESS" | "PARTIAL" | "FAILURE";
export type GatheringResultStatus = "RUNNING" | "SUCCESS" | "SKIPPED" | "FAILURE";

export interface GatheringTaskSummary {
    id: number;
    task_id: string;
    name: string;
    status: GatheringTaskStatus;
    total_devices: number;
    error_type: string;
    error_message: string;
    started_at: string;
    finished_at: string | null;
}

export interface GatheringResultDeviceGroup {
    id: number;
    name: string;
}

export interface GatheringResultDevice {
    id: number;
    name: string;
    ip: string;
    vendor: string | null;
    model: string | null;
    group: GatheringResultDeviceGroup;
}

export interface DeviceGatheringResult {
    id: number;
    task: GatheringTaskSummary;
    device: GatheringResultDevice;
    status: GatheringResultStatus;
    error_type: string;
    error_message: string;
    started_at: string;
    finished_at: string | null;
}

export interface GatheringResultLookups {
    device_groups: GatheringResultDeviceGroup[];
    vendors: string[];
    models: string[];
    task_names: string[];
    error_types: string[];
}

export interface GatheringResultFilters {
    deviceGroup: number | null;
    deviceName: string;
    vendor: string | null;
    model: string | null;
    taskStatus: GatheringTaskStatus | null;
    taskName: string | null;
    taskStartedAfter: Date | null;
    taskStartedBefore: Date | null;
    resultStatus: GatheringResultStatus | null;
    resultStartedAfter: Date | null;
    resultStartedBefore: Date | null;
    errorType: string | null;
    errorMessage: string;
}

export interface GatheringTimelineResponse {
    results: DeviceGatheringResult[];
    truncated: boolean;
}

export type GatheringResultsPage = PaginatedResponse<DeviceGatheringResult>;
