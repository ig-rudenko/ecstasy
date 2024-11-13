export interface HardwareStats {
    cpu?: number[]
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
