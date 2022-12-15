let session_data = $('#brases-data')

/**
 * Он делает вызов AJAX на сервер, а затем обновляет HTML div session_data ответом.
 * @param mac - MAC-адрес устройства
 * @param device_name - Имя устройства, для которого вы хотите получить данные сеанса.
 * @param port - Номер порта устройства, для которого вы хотите получить данные сеанса.
 */
function get_session(mac, device_name, port){
    let data = {
        mac: mac,
        device: device_name,
        port: port,
        ajax: true
    }

    $.ajax({
        url: "/device/session",
        type: 'GET',
        data: data,
        success: function( data ) {
            console.log(data)
            session_data.html(data)
        }
    });
}

/**
 * Отправляет POST-запрос на сервер с данными устройства, порта и MAC адресом абонента, который необходимо сбросить.
 * @param mac - MAC-адрес абонента
 * @param device_name - Название оборудования
 * @param port - Номер порта оборудования
 * @param desc - Описание порта оборудования
 */
function cut_session(mac, device_name, port, desc){
    let data = {
        mac: mac,
        device: device_name,
        port: port,
        desc: desc,
        csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]')[0].value
    }

    console.log(data)
    let re = new RegExp('\n', 'g');

    session_data.html(`
        <div class="text-center">
            <div class="spinner-grow text-primary" role="status" style="width: 100px; height: 100px;">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `)

    $.ajax({
        url: "/device/cut-session",
        type: 'POST',
        data: data,
        success: function( data ) {
            console.log(data)
            $('#toast_message').html(data.message.replace(re, '<br>'))
            $('#toast_color').attr('fill', data.color)
            $('#toast_title').html(data.status)
            $('.toast').toast('show')

            get_session(mac, device_name, port)

        }
    });
}