/* Строка, используемая для добавления на карту информации об авторских правах. */
const copy = "© <a href='/'>Ecstasy</a> Игорь Руденко";
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

let origin_devices_point_format = new Map();


String.prototype.format = function () {
  // store arguments in an array
  var args = arguments;
  // use replace to iterate over the string
  // select the match and check if the related argument is present
  // if yes, replace the match with the argument
  return this.replace(/{([0-9]+)}/g, function (match, index) {
    // check if the argument is present
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
 * Он загружает маркеры из базы данных, затем создает новый маркер для каждого из них и добавляет его на карту.
 */
async function render_markers() {

    const render_data = await load_markers();
    console.log(render_data)

    for (let i = 0; i < render_data.length; i++ ){

        if (render_data[i].type === "zabbix"){

            // Отображаем данные узлов сети Zabbix на карте
            L.geoJSON(render_data[i].features, {
                    pointToLayer: function (feature, latlng) {

                        /* Он проверяет, является ли маркер кругом. */
                        if (feature.properties.figure === "circle"){
                            /* Он создает новый маркер круга и добавляет его к объекту точек. */
                            points.set(feature.id, L.circleMarker(latlng, feature.properties.style)
                                                    .bindTooltip(feature.properties.name)
                                                    .bindPopup(feature.properties.description)
                            )
                            /* Возвращение маркера на карту. */
                            return points.get(feature.id);
                        }
                    }
                }).addTo(layer_control.overlays[render_data[i].name]);

        } else if (render_data[i].type === "geojson") {

            // Настройки по умолчанию для слоя
            let defaultSettings = render_data[i].properties
            // Коллекция
            let features = render_data[i].features.features
            // Слой
            let layer = layer_control.overlays[render_data[i].name]

            for (let j = 0; j < features.length; j++) {

                if (features[j].geometry.type === "Point"){
                    createMarker(
                        features[j],
                        L.GeoJSON.coordsToLatLng(features[j].geometry.coordinates),
                        defaultSettings.Marker
                    ).addTo(layer)

                } else if (features[j].geometry.type === "LineString") {
                    console.log(features[j].geometry.coordinates)
                    createPolyline(
                        features[j],
                        L.GeoJSON.coordsToLatLngs(features[j].geometry.coordinates),
                        defaultSettings.Polygon
                    ).addTo(layer)

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
}

function createPolygon(feature, latlng, defaults) {
    let styleOptions = {
        "fillColor": feature.properties["fill"] || defaults["FillColor"],
        "color": feature.properties["stroke"] || defaults["BorderColor"],
        "weight": feature.properties["stroke-width"] || 2,
        "opacity": feature.properties["stroke-opacity"] || defaults.Opacity,
        "fillOpacity": feature.properties["fill-opacity"] || defaults.Opacity,
    }

    return L.polygon(latlng, styleOptions)
}

function createPolyline(feature, latlng, defaults) {
    let styleOptions = {
        "color": feature.properties.stroke || defaults.BorderColor,
        "weight": feature.properties["stroke-width"] || 2,
        "fillOpacity": feature.properties["stroke-opacity"] || defaults.Opacity,
    }

    return L.polyline(latlng, styleOptions)
}


function createMarker(feature, latlng, defaults) {
    console.log(feature, defaults)

    let popup_text = null
    let tooltip_text = null
    let fillColor = defaults["FillColor"]
    let size = defaults["Size"]
    let icon_name = defaults["IconName"] || "circle-fill"

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

    let circle =  L.marker(latlng, options);
    if (popup_text) {
        circle.bindPopup(format_to_html(popup_text))
    }
    if (tooltip_text) {
        circle.bindTooltip(tooltip_text)
    }
    return circle
}

function format_to_html(string) {
    // Превращаем строки в html, для корректного отображения
    // Заменяем перенос строки на <br>
    //          пробелы на &nbsp;

    let n_re = new RegExp('\n', 'g');

    string = string.replace(n_re, '<br>')
    return string
}
