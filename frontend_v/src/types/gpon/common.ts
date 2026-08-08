/** Стандартный пагинированный ответ Django REST Framework. */
export interface GponPaginatedResponse<T> {
    count: number;
    next: string | null;
    previous: string | null;
    results: T[];
}
