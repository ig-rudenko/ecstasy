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


async function update_status() {
    let response = await fetch(
        window.location.href + "/api/update",
        {
            method: "GET",
            credentials: "same-origin"
        }
    );
    let res = await response.json();

    console.log(res)

    // Список из точек текущих недоступных узлов сети на карте
    let before_down_devices_points = down_devices

    // Новый пустой `map` для будущих недоступных узлов сети на карте
    down_devices = new Map()


    // Если есть проблемные узлы сети
    if (res.problems.length) {

        for (let i = 0; i < res.problems.length; i++) {
            // console.log(res.problems[i])

            // HostID недоступного узла сети
            let host_id = res.problems[i].id

            // Перед тем как изменить точку, сохраняем её предыдущие настройки
            if (!origin_devices_point_format.get(host_id)) {
                origin_devices_point_format.set(
                    host_id,
                    {
                        "fillColor": points.get(host_id).options.fillColor,
                        "popupContent": points.get(host_id)._popup._content
                    }
                )
            }

            // Добавляем текущий недоступный узел сети в набор всех недоступных
            down_devices.set(host_id, points.get(host_id))

            // Текст проблем
            let problems_text = ""
            for (let j = 0; j < res.problems[i].acknowledges.length; j++) {
                let ack_time = res.problems[i].acknowledges[j][1]
                let ack_text = res.problems[i].acknowledges[j][0]
                problems_text += `
                <div>
                    <p><span style="color: #2400ff">${ack_time}</span> -> ${format_to_html(ack_text)}</p>
                </div>`
            }

            // Если уже недоступен и описание проблем не изменилось, то пропускаем
            if (before_down_devices_points.get(host_id)
                && before_down_devices_points.get(host_id)._popup._content === problems_text) {

                // Удаляем из старого набора, так как уже находится в новом
                before_down_devices_points.delete(host_id)

                continue
            }

            // Если уже недоступен, НО описание проблем изменилось
            if (before_down_devices_points.get(host_id)
                && before_down_devices_points.get(host_id)._popup._content !== problems_text) {

                // Удаляем из старого набора, так как уже находится в новом
                before_down_devices_points.delete(host_id)

                // Описание поменялось, обновляем
                down_devices.get(host_id).bindPopup(
                    origin_devices_point_format.get(host_id).popupContent + problems_text,
                    {"maxWidth": 500}
                )

            } else {
                // Новое недоступное оборудование

                let device = down_devices.get(host_id)
                device.removeFrom(map)
                device.options.fillColor = "red"
                device.bindPopup(
                    origin_devices_point_format.get(host_id).popupContent + problems_text,
                    {"maxWidth": 500}
                )
                device.addTo(map)

            }
        }


        let restored_devices_hostid_list = Array.from(before_down_devices_points.keys())

        // Восстанавливаем узлы сети
        for (let i = 0; i < restored_devices_hostid_list.length; i++) {
            let host_id = restored_devices_hostid_list[i]

            let device = before_down_devices_points.get(host_id)
            device.removeFrom(map)

            // Восстанавливаем цвет
            device.options.fillColor = origin_devices_point_format.get(host_id).fillColor
            // Восстанавливаем описание
            device.bindPopup(
                origin_devices_point_format.get(host_id).popupContent,
                {"maxWidth": 500}
            )
            device.addTo(map)
        }
    }

    timer();
}

async function timer() {
    setTimeout(update_status, 15000); // Обновление статуса через 15 сек
}


// При загрузке
document.addEventListener('DOMContentLoaded', async function(){

	let groups_list = await get_groups()

    // Добавляем слои на карту
    for (let i = 0; i < groups_list.groups.length; i++) {
        layer_control.overlays[groups_list.groups[i]] = L.featureGroup(
            {name: groups_list.groups[i]}
        ).addTo(map)
    }


    // Добавляем управление слоями на карту
    L.control.layers(
        layer_control.base_layers,
        layer_control.overlays,
        {"autoZIndex": true, "collapsed": true, "position": "topright"}
    ).addTo(map);

    // Рендерим метки
    await render_markers()

    update_status()
});

// TODO: points["hostid"].options.fillColor = "red"
//       points["hostid"].removeFrom(map)
//       points["hostid"].addTo(map)
