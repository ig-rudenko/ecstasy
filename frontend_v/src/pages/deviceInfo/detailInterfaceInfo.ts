export interface DetailInterfaceInfo {
    data: any,
    type: 'text'|'html'|'mikrotik'|'adsl'|'gpon'|'eltex-gpon'
}

export interface ComplexInterfaceInfoType {
    hasCableDiag: string;
    portConfig: string;
    portDetailInfo: DetailInterfaceInfo;
    portErrors: string;
    portType: string;
}
