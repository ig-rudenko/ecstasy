/* Строка, используемая для добавления на карту информации об авторских правах. */
const copy = "© <a href='https://www.openstreetmap.org/#map=11/44.5795/33.5272'>OpenStreetMap </a>" +
    "<a href='/'>Ecstasy</a> Игорь Руденко";
const url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
const osm = L.tileLayer(url, { attribution: copy });

/* Он создает новый объект карты и устанавливает минимальный уровень масштабирования 5. */
const map = L.map("map", { layers: [osm], minZoom: 5 });

/* Пытается найти ваше местоположение, и если он не может, он устанавливает вид на указанные координаты. */
map.locate()
    .on("locationfound", (e) => map.setView(e.latlng, 14))
    .on("locationerror", () => map.setView([44.6, 33.5], 12));
map.fitWorld();


/* Переменная, используемая для хранения всех слоев, добавляемых на карту. */
let layer_control = {
    base_layers: {
        "openstreetmap": map,
    },
    overlays: {},
};

/* Пустой объект, который будет использоваться для хранения всех маркеров, добавленных на карту. */
let points = new Map();

/* Пустой объект, который будет использоваться для хранения всех Недоступных, добавленных на карту. */
let down_devices = new Map();

/* Карта исходного формата точек устройств. */
let origin_devices_point_format = new Map();


/* Функция, позволяющая использовать метод форматирования строк. */
String.prototype.format = function () {
  var args = arguments;

  return this.replace(/{([0-9]+)}/g, function (match, index) {
    return typeof args[index] == 'undefined' ? match : args[index];
  });
};


/**
 * Получение групп слоев с сервера и возврат их в виде объекта JSON.
 * @returns Promise, которое разрешается в объект JSON.
 */
async function get_groups() {
    let response = await fetch(
        window.location.href + "/api/layers",
        {
          method: 'GET',
          credentials: "same-origin"
        });
    return await response.json();
}


/**
 * Он делает запрос на сервер для маркеров, которые находятся в пределах текущих границ карты.
 * @returns Promise, которое разрешается в объект JSON.
 */
async function load_markers() {

    // Делаем запрос на сервер для получения маркеров.
    let response = await fetch(
        window.location.href + "/api/render",
        {
          method: 'GET',
          credentials: "same-origin"
        });
    return await response.json();
}

/**
 * Загружает маркеры с сервера, затем перебирает маркеры и добавляет их на карту.
 */
async function render_markers() {

    const render_data = await load_markers();
    // console.log(render_data)

    for (let i = 0; i < render_data.length; i++ ){

        /* Проверяем, является ли тип данных zabbix. */
        if (render_data[i].type === "zabbix"){

            // Отображаем данные узлов сети Zabbix на карте
            L.geoJSON(render_data[i].features, {
                    pointToLayer: function (feature, latlng) {

                        /* Он проверяет, является ли маркер кругом. */
                        if (feature.properties.figure === "circle"){
                            /* Он создает новый маркер круга и добавляет его к объекту точек. */
                            points.set(feature.id, {
                                    point: L.circleMarker(latlng, feature.properties.style)
                                                        .bindTooltip(feature.properties.name)
                                                        .bindPopup(feature.properties.description, {maxWidth: 560}),
                                    layer: layer_control.overlays[render_data[i].name],
                                }
                            )
                            /* Возвращение маркера на карту. */
                            return points.get(feature.id).point;
                        }
                    }
                }).addTo(layer_control.overlays[render_data[i].name]);

        /* Проверка, является ли слой слоем geojson. */
        } else if (render_data[i].type === "geojson") {

            // Настройки по умолчанию для слоя
            let defaultSettings = render_data[i].properties
            // Коллекция
            let features = render_data[i].features.features
            // Слой
            let layer = layer_control.overlays[render_data[i].name]

            for (let j = 0; j < features.length; j++) {

                /* Создание маркера из объекта GeoJSON */
                if (features[j].geometry.type === "Point"){
                    createMarker(
                        features[j],
                        L.GeoJSON.coordsToLatLng(features[j].geometry.coordinates),
                        defaultSettings.Marker
                    ).addTo(layer)

                /* Создание полилинии из объекта GeoJSON */
                } else if (features[j].geometry.type === "LineString") {
                    createPolyline(
                        features[j],
                        L.GeoJSON.coordsToLatLngs(features[j].geometry.coordinates),
                        defaultSettings.Polygon
                    ).addTo(layer)

                /* Создание многоугольника из объекта GeoJSON */
                } else if (features[j].geometry.type === "Polygon") {
                    createPolygon(
                        features[j],
                        L.GeoJSON.coordsToLatLngs(features[j].geometry.coordinates[0]),
                        defaultSettings.Polygon
                    ).addTo(layer)
                }
            }
        }
    }

    // Вызываем функцию для восстановления состояния активных слоев при загрузке страницы
    loadLayers();

}

/**
 * Эта функция создает полилинию из объекта GeoJSON, используя значения по умолчанию для цвета, веса и непрозрачности,
 * если объект не имеет этих свойств.
 *  Возвращает полигональный объект Leaflet.
 *
 * @param feature - Объект функции GeoJSON
 * @param latlng - Координаты многоугольника
 * @param defaults - Это словарь значений по умолчанию для полигона.
 * @returns Полигональный объект
 */
function createPolygon(feature, latlng, defaults) {
    /* Создание словаря вариантов стиля полигона. */
    let options = {
        "fillColor": feature.properties["fill"] || defaults["FillColor"],
        "color": feature.properties["stroke"] || defaults["BorderColor"],
        "weight": Number(feature.properties["stroke-width"]) || 2,
        "opacity": feature.properties["stroke-opacity"] || defaults.Opacity,
        "fillOpacity": feature.properties["fill-opacity"] || defaults.Opacity,
    }

    let popup_text = null

    if (feature.properties) {
        popup_text = feature.properties.description
    }

    let polygon = L.polygon(latlng, options)

    if (popup_text) {
        polygon.bindPopup(wrapLinks(format_to_html(popup_text)))
    }

    return polygon
}

/**
 * Эта функция создает полилинию из объекта GeoJSON, используя значения по умолчанию для цвета, веса и непрозрачности,
 * если объект не имеет этих свойств.
 *  Возвращает полигональный объект Leaflet.
 *
 * @param feature - Объект функции GeoJSON
 * @param latlng - массив координат широты/долготы
 * @param defaults - Значения по умолчанию для карты.
 * @returns Полилинейный объект
 */
function createPolyline(feature, latlng, defaults) {
    /* Создание словаря опций стиля для полилинии. */
    let options = {
        "color": feature.properties.stroke || defaults.BorderColor,
        "weight": feature.properties["stroke-width"] || 2,
        "fillOpacity": feature.properties["stroke-opacity"] || defaults.Opacity,
    }

    let popup_text = null

    if (feature.properties) {
        popup_text = feature.properties.description
    }

    let polyline = L.polyline(latlng, options)

    if (popup_text) {
        polyline.bindPopup(wrapLinks(format_to_html(popup_text)))
    }

    /* Возврат полилинейного объекта. */
    return polyline
}


/**
 * Эта функция создает маркер из объекта GeoJSON, используя значения по умолчанию для цвета, имени иконки и размера,
 * если объект не имеет этих свойств.
 * @param feature - функция GeoJSON
 * @param latlng - Широта и долгота маркера
 * @param defaults - словарь значений по умолчанию для маркера
 * @returns Маркер
 */
function createMarker(feature, latlng, defaults) {
    // console.log(feature, defaults)

    let popup_text = null
    let tooltip_text = null
    let fillColor = defaults["FillColor"]
    let size = defaults["Size"]
    let icon_name = defaults["IconName"] || "circle-fill"

    /* Приведенный выше код устанавливает значения по умолчанию для текста всплывающего окна, текста всплывающей подсказки,
    цвета заливки, размера и имени значка. */
    if (feature.properties) {
        popup_text = feature.properties.description

        tooltip_text = feature.properties.iconCaption ||
                         feature.properties.name

        fillColor = feature.properties["marker-color"] ||
                        feature.properties.fillColor ||
                        feature.properties.color || defaults["FillColor"]

        size = feature.properties.radius ||
                     defaults["Size"]

        icon_name = feature.properties.iconName ||
                        defaults["IconName"] || "circle-fill"
    }

    /* Создание новой иконки для маркера. */
    let svgIcon = L.divIcon({
      html: MAP_ICONS[icon_name].format(size, fillColor, defaults["BorderColor"]),
      className: "svg-icon",
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
    });

    let options = {
        "opacity": 1,
        "icon": svgIcon
    }

    /* Создание маркера по координатам широты с указанными параметрами. */
    let marker =  L.marker(latlng, options);

    /* Создание всплывающего окна для маркера. */
    if (popup_text) {
        marker.bindPopup(wrapLinks(format_to_html(popup_text)))
    }
    /* Создание всплывающей подсказки для маркера. */
    if (tooltip_text) {
        marker.bindTooltip(wrapLinks(tooltip_text))
    }
    return marker
}

/**
 * Заменяет символы новой строки разрывами строк HTML.
 * @param string - Строка для форматирования.
 */
function format_to_html(string) {
    // Превращаем строки в html, для корректного отображения
    // Заменяем перенос строки на <br>
    //          пробелы на &nbsp;

    let n_re = new RegExp('\n', 'g');

    string = string.replace(n_re, '<br>')
    return string
}

// Функция, которая принимает текст и возвращает его с обрамленными ссылками
function wrapLinks(text) {
  // Создаем регулярное выражение для поиска ссылок
  let regex = /https?:\/\/\S+/g;
  // Заменяем все найденные ссылки на теги <a href="...">...</a>
  let result = text.replace(regex, function(match) {
    return `<a href="${match}">${match}</a>`;
  });
  // Возвращаем результат
  return result;
}