import {Map as LMap} from 'leaflet';

/**
 * Функция saveLayers() используется для сохранения состояния активных слоев в localStorage. Он перебирает все наложения в
 * объекте `layer_control` и проверяет, добавлены ли они в данный момент на карту. Если добавляется оверлей, его имя
 * добавляется в массив `activeLayers`. Наконец, массив `activeLayers` сохраняется в localStorage с именем ключа, которое
 * включает путь к текущей странице. */
export function saveLayers(mapID: string, map: LMap, overlays: any) {
    let activeLayers = [];
    let keyName = "map_" + mapID
    for (let name in overlays) {
        if (map.hasLayer(overlays[name])) {
            activeLayers.push(name);
        }
    }
    localStorage.setItem(keyName, JSON.stringify(activeLayers));
}

/**
 * Функция loadLayers() используется для восстановления состояния активных слоев из localStorage. Он извлекает массив
 * активных слоев из localStorage, используя имя ключа, которое включает путь к текущей странице. Если в localStorage
 * сохранены активные слои, он перебирает все наложения в объекте `layer_control` и добавляет на карту наложения,
 * находящиеся в массиве activeLayers, и удаляет с карты наложения, которых нет в массиве activeLayers. */
export function loadLayers(mapID: string, map: LMap, overlays: any) {
    let keyName = "map_" + mapID
    let activeLayers = JSON.parse(localStorage.getItem(keyName) || "[]");
    if (activeLayers?.length) {
        for (let name in overlays) {
            if (activeLayers.includes(name)) {
                map.addLayer(overlays[name]);
            } else {
                map.removeLayer(overlays[name]);
            }
        }
    }
}
