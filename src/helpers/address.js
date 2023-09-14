/** address: {
 *    region: "Севастополь",
 *    settlement: "Севастополь",
 *    planStructure: "",
 *    street: "Колобова",
 *    house: "22",
 *    block: 10,
 *    building_type: "building",
 *    floors: 9,
 *    total_entrances: 12
 *  }
 *  @param { Object } address Принимает объект адреса в качестве параметра
 *  @return {string} отформатированная полная строка адреса.
 */
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