export interface HardwareStats {
    cpu?: {
        util: number[],
    },
    flash?: {
        util: number,
    }
    ram?: {
        util: number,
    }
    temp?: {
        status: string,
        value: number
    }
}
