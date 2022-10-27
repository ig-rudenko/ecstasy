var popoverTriggerList
var popoverList

const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))


const isDigit = (string) => {
    return string && /^\d+$/.test(string);
};

let device_port = $('#id-port')[0].value
let device_name = $('#id-device_name')[0].value
let device_port_desc = $('#id-desc')[0].value


function get_macs() {

    if ( document.getElementById('auto-update-macs').checked ) {

        // Если нажато автообновление, то отправляем результаты

        let data = {
            port: device_port,
            device: device_name,
            desc: device_port_desc,
            ajax: 'mac'
        }
        console.log(data)

        $.ajax({
            url: "/device/port/",
            type: 'GET',
            data: data,
            success: function( data ) {
                console.log(data)
                $('#macs-table').html(data.macs)
            }
        });
    }

    timer()
}

// Повторный сбор маков через 10 секунд
let t
function timer() {
    t = setTimeout(get_macs, 10000);
}
timer();

function format_to_html(string) {
    // Превращаем строки в html, для корректного отображения
    // Заменяем перенос строки на <br>
    //          пробелы на &nbsp;

    let space_re = new RegExp(' ', 'g');
    let n_re = new RegExp('\n', 'g');

    string = string.replace(space_re, '&nbsp;').replace(n_re, '<br>')
    return string
}

function start() {
    // Собираем информацию о порте

    let data = {
        port: device_port,
        device: device_name,
        desc: device_port_desc,
        ajax: 'all'
    }
    console.log(data)

    $.ajax({
        url: "/device/port",
        type: 'GET',
        data: data,
        success: function( data ) {
            console.log(data)

            // Конфигурация порта
            if (data.port_config) {
                $('#port-config').html(
                `<button id="port-config-button" type="button" class="btn "
                    data-bs-toggle="popover" data-bs-placement="bottom"
                    data-bs-custom-class="custom-popover"
                    data-bs-title="Текущая"
                >
                <svg class="bi me-2" width="16" height="16" role="img" aria-label="Ecstasy">
                    <use xlink:href="#gear-icon"></use></svg>
                Конфигурация порта</button>`);
                $('#port-config-button').attr('data-bs-content', format_to_html(data.port_config))
            }

            // Ошибки на порту
            if (data.port_errors) {
                $('#port-errors').html(
                `<button id="port-errors" type="button" class="btn "
                    data-bs-toggle="popover" data-bs-placement="right"
                    data-bs-custom-class="custom-popover"
                    data-bs-title="Ошибки"
                    data-bs-content="`+format_to_html(data.port_errors)+`"
                >
                <svg class="bi me-2" width="16" height="16" role="img">
                    <use xlink:href="#warning-icon"></use></svg>
                Ошибки на порту</button>`)
            }

            // Информация на порту
            if (data.port_info) {
                $('#port-info').html(data.port_info+'<hr>')
            }

            if (data.cable_test) {
                $('#cable-diag').html(
                    `<button type="button" class="btn" data-bs-toggle="modal" data-bs-target="#modal-cable-diag"
                        onclick="cable_diag()">
                        <svg class="bi me-2" width="16" height="16" role="img">
                        <use xlink:href="#cable-diag-icon"></use>
                        </svg>
                        Диагностика кабеля
                    </button>`
                )
            }

            // MAC'и на порту
            $('#macs-table').html(data.macs)

            // Тип порта copper, sfp
            if (data.port_type) {
                if (data.port_type === 'SFP') {
                    $('#port-type').css({"backgroundColor": "#3e6cff"}).html('sfp')
                }
                if (data.port_type === 'COPPER') {
                    $('#port-type').css({"backgroundColor": "#b87333"}).html('copper')
                }
                if (data.port_type.includes('COMBO')) {
                    $('#port-type').css({"backgroundColor": "#8133b8"}).html(data.port_type.toLowerCase())
                }
            }

            window.popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
            window.popoverList = popoverTriggerList.map(
                function (popoverTriggerEl) {
                    return new bootstrap.Popover(popoverTriggerEl,{html: true})
                }
            );
        }
    });
}
start()


let cable_diag_load_div = $('#cable-diag-load')  // Блок спиннера загрузки
let cable_diag_info_div = $('#cable-diag-info')  // Блок информации диагностики


function cable_diag() {
    // отправляем запрос на диагностику кабеля порта

    let data = {
        port: device_port,
        device: device_name,
    }

    cable_diag_info_div.prop('hidden', true)  // Показываем загрузку
    cable_diag_load_div.prop('hidden', false)  // Скрываем блок информации

    $.ajax({
        url: "/device/port/cable-diag",
        type: 'GET',
        data: data,
        success: function( data ) {
            console.log(data)

            if (isDigit(data.cable_test.len)) {
                console.log(isDigit(data.cable_test.len))
                $('#cable-length').html("Длина кабеля - " + data.cable_test.len + " м.")  // Длина кабеля
            }

            $('#cable-status').html(data.cable_test.status)  // Статус
            if (data.cable_test.status === 'Up') {
                // Link Up
                $('#cable-status-icon').attr('fill', '#39d286')
            } else if (data.cable_test.status === 'Down') {
                // Link Down
                $('#cable-status-icon').attr('fill', '#ff4b4d')
            } else if (data.cable_test.status === 'Empty') {
                // Нет кабеля
                $('#cable-status-icon').attr('fill', '#19b7f4')
            } else {
                // Другое ?
                $('#cable-status-icon').attr('fill', '#c6bcb0')
            }

            // Отдельно каждую пару
            let pair_info_html = ''

            // Первая пара
            if (data.cable_test.pair1) {
                pair_info_html = pair_info_html + `<div>` + `Пара 1 - ` + data.cable_test.pair1.len + ` м.`
                    + `<img title="` + data.cable_test.pair1.status +
                    `" style="vertical-align: middle; margin: 0 3px 0 10px;" height="40px;" 
                            src="/static/img/rj45-status-` + data.cable_test.pair1.status + `-left.png"></div>`
            }

            // Вторая пара
            if (data.cable_test.pair2) {
                pair_info_html = pair_info_html + `<div>` + `Пара 2 - ` + data.cable_test.pair2.len + ` м.`
                    + `<img title="` + data.cable_test.pair2.status +
                    `" style="vertical-align: middle; margin-left: 12px;" height="40px;"
                            src="/static/img/rj45-status-` + data.cable_test.pair2.status + `-right.png"></div>`
            }

            // Добавляем информацию
            $('#pair-info').html(pair_info_html)

            cable_diag_load_div.prop('hidden', true)  // Скрываем загрузку
            cable_diag_info_div.prop('hidden', false)  // Показываем информацию
        }
    });
}