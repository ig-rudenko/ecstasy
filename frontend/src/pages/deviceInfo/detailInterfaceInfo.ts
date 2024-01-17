class DetailInterfaceInfo {
    constructor(
        public data: any,
        public type: 'text'|'html'|'mikrotik'|'adsl'|'gpon'|'eltex-gpon'
    ) {}
}

class ComplexInterfaceInfo {
    constructor(
        public hasCableDiag: string,
        public portConfig: string,
        public portDetailInfo: DetailInterfaceInfo,
        public portErrors: string,
        public portType: string,
    ) {}
}

export {DetailInterfaceInfo, ComplexInterfaceInfo}
