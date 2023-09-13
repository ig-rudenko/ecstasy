// Принимает объект адреса в качестве параметра и возвращает отформатированную полную строку адреса.
function formatAddress(address) {
    if (!address) return "Выберите"
    let str = ""
    if (address.region !== "Севастополь") str += ` ${address.region},`;
    if (address.settlement !== "Севастополь") str += ` ${address.settlement},`;
    if (address.planStructure.length) str += `СНТ ${address.planStructure},`;
    if (address.street.length) str += ` ${address.street},`;
    str += ` д. ${address.house}`;
    if (address.block) str += `/${address.block}`;
    return str
}

export default formatAddress