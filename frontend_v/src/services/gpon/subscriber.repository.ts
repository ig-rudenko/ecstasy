import api from "@/services/api";
import type {
    CreateSubscriberPayload,
    CustomerDetail,
    GponCustomer,
    GponPaginatedResponse,
    SubscriberConnection,
    SubscriberListItem,
    SubscriberListQuery,
    UpdateCustomerPayload,
} from "@/types/gpon";

/** Загружает пагинированный список абонентских подключений. */
export async function getSubscriberList(
    query: SubscriberListQuery
): Promise<GponPaginatedResponse<SubscriberListItem>> {
    const response = await api.get<GponPaginatedResponse<SubscriberListItem>>("/api/v1/gpon/subscriber-data", {
        params: query,
    });
    return response.data;
}

/** Ищет абонентов по ФИО, компании, телефону или договору. */
export async function getCustomers(
    page: number,
    pageSize: number,
    search?: string
): Promise<GponPaginatedResponse<GponCustomer>> {
    const response = await api.get<GponPaginatedResponse<GponCustomer>>("/api/v1/gpon/customers", {
        params: { page, page_size: pageSize, search },
    });
    return response.data;
}

/** Загружает карточку абонента со всеми подключениями. */
export async function getCustomer(customerId: number): Promise<CustomerDetail> {
    const response = await api.get<CustomerDetail>(`/api/v1/gpon/customers/${customerId}`);
    return response.data;
}

/** Создаёт новое абонентское подключение. */
export async function createSubscriber(payload: CreateSubscriberPayload): Promise<void> {
    await api.post("/api/v1/gpon/subscriber-data", payload);
}

/** Обновляет данные абонента. */
export async function updateCustomer(customerId: number, payload: UpdateCustomerPayload): Promise<CustomerDetail> {
    const response = await api.put<CustomerDetail>(`/api/v1/gpon/customers/${customerId}`, payload);
    return response.data;
}

/** Обновляет абонентское подключение. */
export async function updateSubscriberConnection(
    connection: SubscriberConnection,
    customerId: number
): Promise<SubscriberConnection> {
    const response = await api.put<SubscriberConnection>(`/api/v1/gpon/subscriber-connection/${connection.id}`, {
        ...connection,
        customer: customerId,
    });
    return response.data;
}

/** Удаляет абонентское подключение. */
export async function deleteSubscriberConnection(connectionId: number): Promise<void> {
    await api.delete(`/api/v1/gpon/subscriber-connection/${connectionId}`);
}
