import Customer, {newCustomer} from "../../types/customer";
import Address, {newAddress} from "../../types/address";

class SubscribersData {
    constructor(
        public id: number,
        public address: Address,
        public ontId: number,
        public ip: string,
        public ontSerial: string,
        public ontMac: string,
        public order: string,
        public transit: number,
        public connectedAt: string,
        public services: string[],
        public status: string,
        public end3Port: number,
        public customer: Customer
    ) {}
}

function newSubscriberData(data: any): SubscribersData {
    return new SubscribersData(
        data.id,
        newAddress(data.address),
        data.ont_id,
        data.ip,
        data.ont_serial,
        data.ont_mac,
        data.order,
        data.transit,
        data.connected_at,
        data.services,
        data.status,
        data.end3Port,
        newCustomer(data.customer),
    )
}

export default SubscribersData
export {newSubscriberData}
