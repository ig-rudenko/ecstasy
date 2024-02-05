class Customer {
    constructor(
        public id: number,
        public type: string,
        public firstName: string,
        public surname: string,
        public lastName: string,
        public companyName: string,
        public contract: string,
        public phone: string
    ) {}
}

function newCustomer(data: any): Customer {
    return new Customer(
        data.id,
        data.type,
        data.firstName,
        data.surname,
        data.lastName,
        data.companyName,
        data.contract,
        data.phone,
    )
}

export default Customer
export {newCustomer}
