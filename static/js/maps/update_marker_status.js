
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

            if (!points.get(host_id)) {
                continue
            }

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

        /* Создание списка host_id устройств, которые раньше были отключены, но теперь включены. */
        let restored_devices_hostid_list = Array.from(before_down_devices_points.keys())

        /* Восстановление устройств, которые раньше были отключены, а теперь работают. */
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
