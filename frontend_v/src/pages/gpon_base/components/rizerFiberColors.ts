const RIZER_FIBER_COLORS = [
    { name: "Синий", className: "rizer-color-blue", marked: false },
    { name: "Оранжевый", className: "rizer-color-orange", marked: false },
    { name: "Зеленый", className: "rizer-color-green", marked: false },
    { name: "Коричневый", className: "rizer-color-brown", marked: false },
    { name: "Серый", className: "rizer-color-grey", marked: false },
    { name: "Белый", className: "rizer-color-white", marked: false },
    { name: "Красный", className: "rizer-color-red", marked: false },
    { name: "Черный", className: "rizer-color-black", marked: false },
    { name: "Желтый", className: "rizer-color-yellow", marked: false },
    { name: "Фиолетовый", className: "rizer-color-violet", marked: false },
    { name: "Розовый", className: "rizer-color-pink", marked: false },
    { name: "Бирюзовый", className: "rizer-color-aqua", marked: false },
    { name: "Синий", className: "rizer-color-blue", marked: true },
    { name: "Оранжевый", className: "rizer-color-orange", marked: true },
    { name: "Зеленый", className: "rizer-color-green", marked: true },
    { name: "Коричневый", className: "rizer-color-brown", marked: true },
    { name: "Серый", className: "rizer-color-grey", marked: true },
    { name: "Белый", className: "rizer-color-white", marked: true },
    { name: "Красный", className: "rizer-color-red", marked: true },
    { name: "Натуральный (прозрачный)", className: "rizer-color-natural", marked: false },
    { name: "Желтый", className: "rizer-color-yellow", marked: true },
    { name: "Фиолетовый", className: "rizer-color-violet", marked: true },
    { name: "Розовый", className: "rizer-color-pink", marked: true },
    { name: "Бирюзовый", className: "rizer-color-aqua", marked: true },
];

export function getRizerFiberInfo(num: number) {
    const index = Number(num) - 1;
    if (!Number.isFinite(index) || index < 0 || index >= RIZER_FIBER_COLORS.length) {
        return null;
    }
    return RIZER_FIBER_COLORS[index];
}
