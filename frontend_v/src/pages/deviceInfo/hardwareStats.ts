export interface HardwareStats {
    cpu?: {
        util: number[];
    };
    flash?: {
        util: number;
    };
    ram?: {
        util: number;
    };
    temp?: {
        status: string;
        value: number;
    };
}

export function hwStatsNotEmpty(hardwareStats: HardwareStats | null): boolean {
    if (!hardwareStats) return false;
    return Boolean(
        hardwareStats.cpu?.util || hardwareStats.flash?.util || hardwareStats.ram?.util || hardwareStats.temp?.value
    );
}
