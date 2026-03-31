import {formatAddress} from "@/formats";
import SubscribersData, {newSubscriberData} from "@/pages/deviceInfo/subscribersData";
import {Customer} from "@/types/customer";

export interface OltSubscriberSummary {
  customers: { id: number, fullName: string }[]
  addresses: string[]
  services: string[]
  transits: string[]
}

export type OltSubscribersByOnt = Record<number, OltSubscriberSummary>;

function customerFullName(customer: Customer) {
  if (customer.companyName && customer.companyName.length) {
    return customer.companyName;
  }
  return [customer.surname, customer.firstName, customer.lastName].filter(Boolean).join(" ");
}

function formatSubscriberAddress(subscriber: SubscribersData) {
  const address = subscriber.address;
  let addressString = formatAddress(address);

  if (address.apartment) {
    addressString += ` кв. ${address.apartment}`;
  }
  if (address.floor) {
    addressString += ` (${address.floor} этаж)`;
  }

  return addressString;
}

export function buildOltSubscribersByOnt(subscribers: any[]): OltSubscribersByOnt {
  const grouped: OltSubscribersByOnt = {};

  for (const rawSubscriber of subscribers) {
    const subscriber = newSubscriberData(rawSubscriber);
    const ontId = subscriber.ontId;

    if (!grouped[ontId]) {
      grouped[ontId] = {
        customers: [],
        addresses: [],
        services: [],
        transits: [],
      };
    }

    grouped[ontId].customers.push({
      id: subscriber.customer.id,
      fullName: customerFullName(subscriber.customer),
    });
    grouped[ontId].addresses.push(formatSubscriberAddress(subscriber));
    grouped[ontId].services.push(subscriber.services.join(", "));
    grouped[ontId].transits.push(String(subscriber.transit));
  }

  return grouped;
}
