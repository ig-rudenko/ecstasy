/** Статистика количества абонентов на OLT-порту. */
export interface OltPortSubscriberStatistic {
    oltPort: string;
    count: number;
}

/** Параметры запроса статистики по OLT-портам. */
export interface OltPortStatisticQuery {
    page: number;
    page_size?: number;
}
