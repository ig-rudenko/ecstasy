
/**
 * Функция saveLayers() используется для сохранения состояния активных слоев в localStorage. Он перебирает все наложения в
 * объекте `layer_control` и проверяет, добавлены ли они в данный момент на карту. Если добавляется оверлей, его имя
 * добавляется в массив `activeLayers`. Наконец, массив `activeLayers` сохраняется в localStorage с именем ключа, которое
 * включает путь к текущей странице. */
function saveLayers() {
    let activeLayers = [];
    let keyName = "map_" + document.location.pathname.split('/')[2] + "_activeLayers"
    for (let name in layer_control.overlays) {
        if (map.hasLayer(layer_control.overlays[name])) {
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
function loadLayers() {
    let keyName = "map_" + document.location.pathname.split('/')[2] + "_activeLayers"
    let activeLayers = JSON.parse(localStorage.getItem(keyName));
    if (activeLayers) {
        for (let name in layer_control.overlays) {
            if (activeLayers.includes(name)) {
                map.addLayer(layer_control.overlays[name]);
            } else {
                map.removeLayer(layer_control.overlays[name]);
            }
        }
    }
}

// Подписываемся на событие изменения слоев и вызываем функцию для сохранения состояния активных слоев при каждом изменении
map.on('overlayadd overlayremove', saveLayers);
