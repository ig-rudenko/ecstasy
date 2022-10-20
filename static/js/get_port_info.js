var popoverTriggerList
var popoverList

const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

function get_macs() {

    if ( document.getElementById('auto-update-macs').checked ) {

        // Если нажато автообновление, то отправляем результаты

        let data = {
            port: $('#id-port').value,
            device: $('#id-device_name').value,
            desc: $('#id-desc').value,
            ajax: 'mac',
            csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]')[0].value
        }
        console.log(data)

        $.ajax({
            url: "/device/port/mac",
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
function start() {

    let data = {
        port: $('#id-port')[0].value,
        device: $('#id-device_name')[0].value,
        desc: $('#id-desc')[0].value,
        ajax: 'all',
        csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]')[0].value
    }
    console.log(data)

    $.ajax({
        url: "/device/port/mac",
        type: 'GET',
        data: data,
        success: function( data ) {
            console.log(data)

            var re = new RegExp('\n', 'g');

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
                $('#port-config-button').attr('data-bs-content', data.port_config.replace(re, '<br>'))
            }

            console.log(data.port_errors)
            if (data.port_errors) {
                $('#port-errors').html(
                `<button id="port-errors" type="button" class="btn "
                    data-bs-toggle="popover" data-bs-placement="right"
                    data-bs-custom-class="custom-popover"
                    data-bs-title="Ошибки"
                    data-bs-content="`+data.port_errors.replace(RegExp(' ', 'g'), '&nbsp;').replace(re, '<br>')+`"
                >
                <svg class="bi me-2" width="16" height="16" role="img">
                    <use xlink:href="#warning-icon"></use></svg>
                Ошибки на порту</button>`)
            }

            if (data.port_info) {
                $('#port-info').html(data.port_info+'<hr>')
            }
            $('#macs-table').html(data.macs)

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