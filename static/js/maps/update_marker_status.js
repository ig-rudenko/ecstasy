
async function update_status() {
    let response = await fetch(
        window.location.href + "/api/update",
        {
            method: "GET",
            credentials: "same-origin"
        }
    );
    let res = await response.json();

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

            if (!points.get(host_id)) {
                continue
            }

            // Перед тем как изменить точку, сохраняем её предыдущие настройки
            if (!origin_devices_point_format.get(host_id)) {
                const origin_points_data = points.get(host_id)
                origin_devices_point_format.set(
                    host_id,
                    {
                        "fillColor": origin_points_data.point.options.fillColor,
                        "popupContent": origin_points_data.point._popup._content,
                        "layer": origin_points_data.layer
                    }
                )
            }

            // Добавляем текущий недоступный узел сети в набор всех недоступных
            let unavailable_point = points.get(host_id).point
            down_devices.set(host_id, unavailable_point)

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
                unavailable_point.bindPopup(
                    origin_devices_point_format.get(host_id).popupContent + problems_text,
                    {"maxWidth": 500}
                )

            } else {
                // Новое недоступное оборудование
                let origin_layer = origin_devices_point_format.get(host_id).layer

                // Удаляем из карты
                unavailable_point.removeFrom(map)
                unavailable_point.options.fillColor = "red" // Меняем цвет
                unavailable_point.bindPopup(  // Меняем описание
                    origin_devices_point_format.get(host_id).popupContent + problems_text,
                    {"maxWidth": 500}
                )

                // Добавляем метку на её слой
                unavailable_point.addTo(origin_layer)

            }
        }

        /* Создание списка host_id устройств, которые раньше были отключены, но теперь включены. */
        let restored_devices_hostid_list = Array.from(before_down_devices_points.keys())

        /* Восстановление устройств, которые раньше были отключены, а теперь работают. */
        for (let host_id of restored_devices_hostid_list) {
            let origin = origin_devices_point_format.get(host_id)  //
            let device = before_down_devices_points.get(host_id)

            device.removeFrom(map)
            device.options.fillColor = origin.fillColor  // Восстанавливаем цвет
            device.bindPopup(origin.popupContent, {"maxWidth": 500})  // Восстанавливаем описание
            device.addTo(origin.layer)  // Добавляем метку на её слой

        }
    }

    await timer();
}

async function timer() {
    setTimeout(update_status, 15000); // Обновление статуса через 15 сек
}
