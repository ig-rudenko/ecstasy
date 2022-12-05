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


// Скрываем contributors (правый нижний угол)
// document.getElementsByClassName("leaflet-attribution-flag")[0].innerHTML = ""


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

            let features = render_data[i].features.features
            let layer = layer_control.overlays[render_data[i].name]
            console.log(layer)

            for (let j = 0; j < features.length; j++) {

                if (features[j].geometry.type === "Point"){
                    createMarker(
                        features[j],
                        L.GeoJSON.coordsToLatLng(features[j].geometry.coordinates)
                    ).addTo(layer)

                } else if (features[j].geometry.type === "LineString") {
                    console.log(features[j].geometry.coordinates)
                    createPolyline(
                        features[j],
                        L.GeoJSON.coordsToLatLngs(features[j].geometry.coordinates)
                    ).addTo(layer)

                } else if (features[j].geometry.type === "Polygon") {
                    createPolygon(
                        features[j],
                        L.GeoJSON.coordsToLatLngs(features[j].geometry.coordinates[0])
                    ).addTo(layer)
                }
            }
        }
    }
}

function createPolygon(feature, latlng) {
    console.log(feature, latlng)
    let styleOptions = {
        "fillColor": feature.properties["fill"],
        "color": feature.properties["stroke"],
        "weight": feature.properties["stroke-width"],
        "opacity": feature.properties["stroke-opacity"],
        "fillOpacity": feature.properties["fill-opacity"],
    }

    return L.polygon(latlng, styleOptions)
}

function createPolyline(feature, latlng) {
    let styleOptions = {
        "color": feature.properties.stroke,
        "weight": feature.properties["stroke-width"],
        "fillOpacity": feature.properties["stroke-opacity"],
    }

    return L.polyline(latlng, styleOptions)
}


function createMarker(feature, latlng) {
    console.log(feature, latlng)
    let popup_text = feature.properties.description ||
                     feature.properties.name ||
                     ""
    let tooltip_text = feature.properties.iconCaption ||
                     feature.properties.name

    let fillColor = feature.properties["marker-color"] ||
                    feature.properties.fillColor ||
                    feature.properties.color

    let styleOptions = {
        "radius": 7,
        "fillColor": fillColor,
        "color": fillColor,
        "weight": 1,
        "opacity": 1,
        "fillOpacity": 1,
    }

    let circle =  L.circleMarker(latlng, styleOptions);
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
