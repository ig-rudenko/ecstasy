class Customer {
    constructor(
        id: number,
        type: string,
        firstName: string,
        surname: string,
        lastName: string,
        companyName: string,
        contract: string,
        phone: string
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
