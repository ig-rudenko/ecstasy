import type { GponAddress } from "@/types/gpon/address";
import type { End3WithCapability, TechCapability, TechCapabilityStatus } from "@/types/gpon/tech-data";

/** Поддерживаемый тип абонента. */
export type CustomerType = "person" | "company" | "contract" | "state";

/** Абонент GPON. */
export interface GponCustomer {
    id: number | null;
    type: CustomerType;
    firstName: string | null;
    surname: string | null;
    lastName: string | null;
    companyName: string | null;
    contract: string | null;
    phone: string | null;
}

/** OLT connection summary embedded in a subscriber connection. */
export interface SubscriberHouseOltState {
    id: number;
    houseAddress: GponAddress;
    deviceName: string;
    devicePort: string;
}

/** Подключение абонента в детальном представлении. */
export interface SubscriberConnection {
    id: number;
    address: GponAddress;
    ip: string | null;
    ont_id: number | null;
    ont_serial: string | null;
    ont_mac: string | null;
    order: string | null;
    transit: number | null;
    description: string | null;
    connected_at: string | null;
    services: string[];
    status: TechCapabilityStatus;
    tech_capability_id: number;
    houseOLTState: SubscriberHouseOltState | null;
    end3: End3WithCapability;
    end3Port: number;
}

/** Абонент со всеми подключениями. */
export interface CustomerDetail extends GponCustomer {
    id: number;
    connections: SubscriberConnection[];
}

/** Строка списка абонентских подключений. */
export interface SubscriberListItem extends SubscriberConnection {
    customer: GponCustomer;
}

/** Фильтры списка абонентских подключений. */
export interface SubscriberListQuery {
    page: number;
    page_size: number;
    general: string;
    region: string;
    settlement: string;
    planStructure: string;
    street: string;
    house: string;
    block: string;
    customerName: string;
    contract: string;
}

/** Данные создания абонентского подключения. */
export interface CreateSubscriberPayload {
    customer: GponCustomer;
    address: GponAddress;
    tech_capability: number;
    description: string | null;
    transit: number | null;
    order: string | null;
    services: string[];
    ip: string | null;
    ont_id: number | null;
    ont_serial: string | null;
    ont_mac: string | null;
    connected_at: string | null;
}

/** Технический выбор в форме нового подключения. */
export interface SubscriberTechSelection {
    deviceName: string | null;
    devicePort: string | null;
    address: GponAddress | null;
    end3: End3WithCapability | null;
    end3Port: TechCapability | null;
}

/** Данные обновления карточки абонента. */
export type UpdateCustomerPayload = Omit<GponCustomer, "id">;
