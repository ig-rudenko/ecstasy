export interface MapViewPosition {
    lat: number;
    lng: number;
    zoom: number;
}

/**
 * Возвращает положение карты из query-параметров или null для некорректного набора.
 */
export function parseMapViewQuery(query: Record<string, unknown>, minZoom: number, maxZoom: number) {
    const lat = parseQueryNumber(query.lat);
    const lng = parseQueryNumber(query.lng);
    const zoom = parseQueryNumber(query.zoom);

    if (
        lat === null ||
        lng === null ||
        zoom === null ||
        lat < -90 ||
        lat > 90 ||
        lng < -180 ||
        lng > 180 ||
        zoom < minZoom ||
        zoom > maxZoom
    ) {
        return null;
    }

    return { lat, lng, zoom };
}

/**
 * Формирует компактные query-параметры положения карты.
 */
export function createMapViewQuery(position: MapViewPosition) {
    return {
        lat: formatCoordinate(position.lat),
        lng: formatCoordinate(position.lng),
        zoom: String(position.zoom),
    };
}

/**
 * Преобразует одиночное строковое значение query-параметра в число.
 */
function parseQueryNumber(value: unknown) {
    if (typeof value !== "string" || value.trim() === "") {
        return null;
    }

    const number = Number(value);
    return Number.isFinite(number) ? number : null;
}

/**
 * Ограничивает точность координаты шестью знаками после запятой.
 */
function formatCoordinate(value: number) {
    return String(Number(value.toFixed(6)));
}
