export interface Paginator<T> {
    count: number;
    next: string | null;
    previous: string | null;
    results: T[];
}

export type PaginatedResponse<T> = Paginator<T>;
