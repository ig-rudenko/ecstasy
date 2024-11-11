export interface Paginator<T> {
    count: number;
    next: string;
    previous: string;
    results: T[];
}
