import api from "@/services/api";
import type { GponPaginatedResponse, OltPortStatisticQuery, OltPortSubscriberStatistic } from "@/types/gpon";

type OltPortStatisticResponse = GponPaginatedResponse<OltPortSubscriberStatistic> | OltPortSubscriberStatistic[];

/** Loads one statistics page while supporting the legacy unpaginated response. */
async function getOltPortSubscriberStatisticsPage(
    deviceName: string,
    query: OltPortStatisticQuery
): Promise<OltPortStatisticResponse> {
    const response = await api.get<OltPortStatisticResponse>(
        `/api/v1/gpon/statistic/subscribers-count/${encodeURIComponent(deviceName)}`,
        { params: query }
    );
    return response.data;
}

/** Loads all subscriber counts for the OLT ports of a device. */
export async function getOltPortSubscriberStatistics(deviceName: string): Promise<OltPortSubscriberStatistic[]> {
    const firstPage = await getOltPortSubscriberStatisticsPage(deviceName, { page: 1 });
    if (Array.isArray(firstPage)) {
        return firstPage;
    }

    const statistics = [...firstPage.results];
    let currentPage = firstPage;
    let page = 2;
    while (currentPage.next && statistics.length < currentPage.count) {
        const nextPage = await getOltPortSubscriberStatisticsPage(deviceName, { page });
        if (Array.isArray(nextPage)) {
            statistics.push(...nextPage);
            break;
        }
        currentPage = nextPage;
        statistics.push(...currentPage.results);
        page += 1;
    }
    return statistics;
}
