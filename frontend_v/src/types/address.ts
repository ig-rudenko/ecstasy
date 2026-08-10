export interface Address {
    region: string;
    settlement: string;
    planStructure: string;
    street: string;
    house: string;
    block: number | null;
    floor?: number | null;
    apartment?: number | null;
}
