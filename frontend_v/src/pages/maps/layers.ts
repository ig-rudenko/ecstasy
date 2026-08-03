import type { Layer, Map as LMap } from "leaflet";

interface MapStorageState {
    tiles?: string;
    groups: string[];
}

type LayersObject = Record<string, Layer>;

function getKeyName(mapID: string) {
    return "map_" + mapID;
}

function getStringList(value: unknown): string[] {
    if (!Array.isArray(value)) {
        return [];
    }

    return value.filter((item): item is string => typeof item === "string");
}

function parseMapStorageState(value: string | null): MapStorageState {
    if (!value) {
        return { groups: [] };
    }

    try {
        const parsed = JSON.parse(value);

        if (Array.isArray(parsed)) {
            return { groups: getStringList(parsed) };
        }

        if (parsed && typeof parsed === "object") {
            const state = parsed as { tiles?: unknown; tileLayer?: unknown; groups?: unknown };
            let tiles: string | undefined;

            if (typeof state.tiles === "string") {
                tiles = state.tiles;
            } else if (typeof state.tileLayer === "string") {
                tiles = state.tileLayer;
            }

            return {
                tiles,
                groups: getStringList(state.groups),
            };
        }
    } catch {
        return { groups: [] };
    }

    return { groups: [] };
}

/**
 * Функция saveLayers() используется для сохранения состояния активных слоев и подложки в localStorage. Он перебирает все наложения в
 * объекте `layer_control` и проверяет, добавлены ли они в данный момент на карту. Если добавляется оверлей, его имя
 * добавляется в массив `groups`. Наконец, состояние карты сохраняется в localStorage с именем ключа, которое
 * включает путь к текущей странице. */
export function saveLayers(mapID: string, map: LMap, overlays: LayersObject, tiles?: string) {
    let groups: string[] = [];
    let keyName = getKeyName(mapID);
    let previousState = parseMapStorageState(localStorage.getItem(keyName));

    for (let name in overlays) {
        if (map.hasLayer(overlays[name])) {
            groups.push(name);
        }
    }
    localStorage.setItem(keyName, JSON.stringify({ tiles: tiles || previousState.tiles, groups }));
}

/**
 * Функция loadLayers() используется для восстановления состояния активных слоев и подложки из localStorage.
 * Он извлекает состояние карты, используя имя ключа, которое включает путь к текущей странице.
 * Если в localStorage сохранены активные слои, он перебирает все наложения в объекте `layer_control` и добавляет
 * на карту наложения, находящиеся в массиве groups, и удаляет с карты наложения, которых нет в массиве groups. */
export function loadLayers(
    mapID: string,
    map: LMap,
    overlays: LayersObject,
    tileLayers?: LayersObject
): MapStorageState {
    let keyName = getKeyName(mapID);
    let state = parseMapStorageState(localStorage.getItem(keyName));

    if (state.tiles && tileLayers?.[state.tiles]) {
        for (let name in tileLayers) {
            map.removeLayer(tileLayers[name]);
        }
        map.addLayer(tileLayers[state.tiles]);
    }

    if (state.groups.length) {
        for (let name in overlays) {
            if (state.groups.includes(name)) {
                map.addLayer(overlays[name]);
            } else {
                map.removeLayer(overlays[name]);
            }
        }
    }

    return state;
}
