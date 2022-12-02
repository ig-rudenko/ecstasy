/* Строка, используемая для добавления на карту информации об авторских правах. */
const copy = "© <a href='/'>Ecstasy</a> Игорь Руденко";
const url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
const osm = L.tileLayer(url, { attribution: copy });

/* Он создает новый объект карты и устанавливает минимальный уровень масштабирования 5. */
const map = L.map("map", { layers: [osm], minZoom: 5 });

/* Пытается найти ваше местоположение, и если он не может, он устанавливает вид на указанные координаты. */
map.locate()
    .on("locationfound", (e) => map.setView(e.latlng, 16))
    .on("locationerror", () => map.setView([44.6, 33.5], 12));
map.fitWorld();


// Скрываем contributors (правый нижний угол)
document.getElementsByClassName("leaflet-attribution-flag")[0].innerHTML = ""


const svgIcon = L.divIcon({
  html: `
<svg
  width="24"
  height="40"
  viewBox="0 0 100 100"
  version="1.1"
  preserveAspectRatio="none"
  xmlns="http://www.w3.org/2000/svg"
>
  <path d="M0 0 L50 100 L100 0 Z" fill="#7A8BE7"></path>
</svg>`,
  className: "svg-icon",
  iconSize: [10, 20],
  iconAnchor: [12, 40],
});


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
    //?in_bbox=${map.getBounds().toBBoxString()}

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

    const markers = await load_markers();
    console.log(markers)

    L.geoJSON(markers, {
            pointToLayer: function (feature, latlng) {
                console.log(feature, latlng)
                /* Он проверяет, является ли маркер кругом. */
                if (feature.properties.figure === "circle"){
                    /* Он создает новый маркер круга и добавляет его к объекту точек. */
                    points.set(feature.id, L.circleMarker(latlng, feature.properties.style)
                                            .bindTooltip(feature.properties.name)
                                            .bindPopup(feature.properties.description)
                                            .addTo(layer_control.overlays[feature.properties.group])
                    )
                    /* Возвращение маркера на карту. */
                    return points.get(feature.id);
                }
            }
        });
}

function format_to_html(string) {
    // Превращаем строки в html, для корректного отображения
    // Заменяем перенос строки на <br>
    //          пробелы на &nbsp;

    let space_re = new RegExp(' ', 'g');
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

    // Список из ID текущих недоступных узлов сети на карте
    let before_down_devices_ids_list = Array.from(down_devices.keys())

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
    console.log(groups_list)

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

    // Действие при изменении карты
    // map.on("moveend", update_status);

    update_status()
    timer();
});

// TODO: points["hostid"].options.fillColor = "red"
//       points["hostid"].removeFrom(map)
//       points["hostid"].addTo(map)
