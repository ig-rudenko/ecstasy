/** Ошибка, отображаемая в GPON-компонентах. */
export interface GponErrorState {
    status: number | string | null;
    message: string | null;
}

/** Параметры события пагинации PrimeVue. */
export interface GponPageEvent {
    page: number;
    rows?: number;
}

/** Параметры ленивой загрузки PrimeVue Select. */
export interface GponLazyLoadEvent {
    last: number;
}

/** Параметры фильтрации PrimeVue Select. */
export interface GponFilterEvent {
    value?: string;
}
