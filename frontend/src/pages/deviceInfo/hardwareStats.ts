class Utilization {
    constructor(public util: number) {}
}
class UtilizationList {
    constructor(public util: Array<number>) {}
}

class Temp {
    constructor(public status: string, public value: number) {}
}

class HardwareStats {
    constructor(
        public cpu: UtilizationList | null,
        public flash: Utilization | null,
        public ram: Utilization | null,
        public temp: Temp | null,
    ) {}
}

function newHardwareStats(data: any): HardwareStats {
    return new HardwareStats(
        data.cpu?new UtilizationList(data.cpu.util || []):null,
        data.flash?new Utilization(data.flash.util):null,
        data.ram?new Utilization(data.ram.util):null,
        data.temp?new Temp(data.temp.status, data.temp.value):null,
    )
}

export {HardwareStats, newHardwareStats}
