import {Address} from "@/types/address";

export function verboseDatetime(date: string): string {
    // multiplied by 1000 so that the argument is in milliseconds, not seconds
    const dateObject = new Date(date);
    return dateObject.toLocaleString("ru-RU",)
}

export function getAvatar(username: string, image?: string, size: number = 64) {
    if (image) return image;
    return `https://ui-avatars.com/api/?size=${size}&name=${username}&font-size=0.33&background=random&rounded=true`
}

export function textToHtml(str: string, formatSpaces: boolean = true): string {
    let space_re = new RegExp(' ', 'g');
    let n_re = new RegExp('\n', 'g');
    if (formatSpaces) str = str.replace(space_re, '&nbsp;');
    str = str.replace(n_re, '<br>')
    return str
}

/** Выделяем тегом <mark></mark> часть в описании, которая совпадает с паттерном поиска */
export function markText(desc: string, pattern: string): string {
    return desc.replace(new RegExp(pattern, 'ig'), s => '<mark>' + s + '</mark>')
}

export function formatAddress(address: Address): string {
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

// Функция, которая принимает текст и возвращает его с обрамленными ссылками
export function wrapLinks(text: string): string {
    // Создаем регулярное выражение для поиска ссылок.
    let regex = /https?:\/\/\S+/g;
    // Заменяем все найденные ссылки на теги: `<a href="...">...</a>`.
    // Возвращаем результат.
    return text.replace(regex, match => `<a href="${match}">${match}</a>`);
}


export function strFormatArgs(str: string, ...args: any[]) {
    return str.replace(/{([0-9]+)}/g, function (match, index) {
        return typeof args[index] == 'undefined' ? match : args[index];
    })
}
