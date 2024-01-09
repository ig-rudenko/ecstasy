class Address {
    constructor(
        public region: string,
        public settlement: string,
        public planStructure: string,
        public street: string,
        public house: string,
        public block: number,
        public floor: number,
        public apartment: number
    ) {}
}

function newAddress(data: any): Address {
    return new Address(
        data.region,
        data.settlement,
        data.planStructure,
        data.street,
        data.house,
        data.block,
        data.floor,
        data.apartment,
    )
}

export default Address
export {newAddress}
