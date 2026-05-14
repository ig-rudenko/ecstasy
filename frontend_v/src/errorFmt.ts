import { AxiosError, isAxiosError } from "axios";

export interface ProblemErrorItem {
    detail?: unknown;
    field?: unknown;
    [key: string]: unknown;
}

export interface ProblemDetails {
    type: string;
    title: string;
    status: number;
    detail?: string;
    instance?: string;
    errors?: unknown;
    [key: string]: unknown;
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function isProblemDetails(value: unknown): value is ProblemDetails {
    return (
        isRecord(value) &&
        typeof value.type === "string" &&
        typeof value.title === "string" &&
        typeof value.status === "number"
    );
}

function stringifyValue(value: unknown): string {
    if (value == null) return "";
    if (typeof value === "string") return value;
    if (Array.isArray(value)) return value.map(stringifyValue).filter(Boolean).join("<br>");
    if (isRecord(value) && "detail" in value) return stringifyValue(value.detail);
    if (isRecord(value) && "message" in value) return stringifyValue(value.message);
    return JSON.stringify(value);
}

function formatProblemErrorItem(error: unknown): string {
    if (!isRecord(error)) return stringifyValue(error);

    const detail = stringifyValue(error.detail || error.message || error);
    const field = stringifyValue(error.field);
    return field ? `${field}: ${detail}` : detail;
}

export function formatProblemErrors(errors: unknown): string {
    if (!errors) return "";

    if (Array.isArray(errors)) {
        return errors.map(formatProblemErrorItem).filter(Boolean).join("<br>");
    }

    if (isRecord(errors)) {
        return Object.entries(errors)
            .map(([field, value]) => {
                const detail = stringifyValue(value);
                return detail ? `${field}: ${detail}` : field;
            })
            .join("<br>");
    }

    return stringifyValue(errors);
}

export function getProblemDetails(error: unknown): ProblemDetails | null {
    if (isProblemDetails(error)) return error;
    if (!isAxiosError(error)) return null;

    const data = error.response?.data;
    return isProblemDetails(data) ? data : null;
}

export function getErrorStatus(error: unknown): number | undefined {
    const problem = getProblemDetails(error);
    if (problem) return problem.status;
    if (isAxiosError(error)) return error.response?.status;
    return undefined;
}

export function getErrorSummary(error: unknown): string {
    const problem = getProblemDetails(error);
    if (problem) return problem.title;
    const status = getErrorStatus(error);
    return status ? `HTTP ${status}` : "Ошибка";
}

export function getErrorData(error: unknown): unknown {
    if (isAxiosError(error)) return error.response?.data;
    return error;
}

export function getErrorFields(error: unknown): Record<string, string> {
    const problem = getProblemDetails(error);
    if (problem) {
        const fields: Record<string, string> = {};
        if (Array.isArray(problem.errors)) {
            for (const item of problem.errors) {
                if (!isRecord(item)) continue;
                const field = stringifyValue(item.field) || "serverError";
                fields[field] = stringifyValue(item.detail || item);
            }
        } else if (isRecord(problem.errors)) {
            for (const [field, value] of Object.entries(problem.errors)) {
                fields[field] = stringifyValue(value);
            }
        }
        if (!Object.keys(fields).length) fields.serverError = getVerboseAxiosError(error);
        return fields;
    }

    const data = getErrorData(error);
    if (isRecord(data)) {
        return Object.fromEntries(Object.entries(data).map(([field, value]) => [field, stringifyValue(value)]));
    }

    return { serverError: getVerboseAxiosError(error) };
}

function getLegacyAxiosError(error: AxiosError<unknown>): string {
    const data = error.response?.data;
    if (!isRecord(data)) return error.message;

    if ("detail" in data || "error" in data) {
        return stringifyValue(data.detail || data.error);
    }

    return stringifyValue(data) || error.message;
}

function getVerboseAxiosError(error: unknown): string {
    const problem = getProblemDetails(error);
    if (problem) {
        const parts = [problem.detail, formatProblemErrors(problem.errors)].filter(Boolean);
        return parts.join("<br>");
    }

    if (isAxiosError(error)) return getLegacyAxiosError(error);
    if (error instanceof Error) return error.message;
    return stringifyValue(error);
}

export default getVerboseAxiosError;
