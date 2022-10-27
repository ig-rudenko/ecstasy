let csrf_token = $('input[name=csrfmiddlewaretoken]')[0].value
let device_name_ = $("name").html()
let port_description = $("description")

function reload_port(port, desc, status, save_config='yes') {
    let data = {
            port: port,                 // Сам порт
            device: device_name_,       // Имя оборудования
            desc: desc,                 // Описание порта
            status: status,             // Что сделать с портом
            save: save_config,          // Сохранить конфигурацию после действия?
            csrfmiddlewaretoken: csrf_token
        }
    $.ajax( {
        url: "/device/port/reload",
        type: 'POST',
        data: data,
        success: function( data ) {
            $('#toast_message').html(data.message)
            $('#toast_color').attr('fill', data.color)
            $('#toast_title').html(data.status)
            $('.toast').toast('show')
        },
        error: function (data) {
            console.log(data)
        }
    });
}

modal_text = document.getElementById('modal-text')
modal_port_desc = document.getElementById('modal-port-desc')

function update_modal(port, desc, status) {
    let text = ''
    if (status === 'reload') {
        text = `Вы уверены, что хотите <br>перезагрузить 
         <svg class="bi me-2" width="24" height="24" role="img">
             <use xlink:href="#port-reload-icon"></use>
         </svg>порт `
    }
    if (status === 'up') {
        text = `Вы уверены, что хотите <br>включить 
         <svg class="bi me-2" width="24" height="24" role="img">
             <use xlink:href="#port-up-icon"></use>
         </svg>порт `
    }
    if (status === 'down') {
        text = `Вы уверены, что хотите <br>выключить 
         <svg class="bi me-2" width="24" height="24" role="img">
             <use xlink:href="#port-down-icon"></use>
         </svg>порт `
    }

    modal_text.innerHTML = text + port + '?'
    modal_port_desc.innerHTML = desc

    $('#modal-button-no-save').attr('onclick', `reload_port("${port}", "${desc}", "${status}", "no")`)
    $('#modal-button-save').attr('onclick', `reload_port("${port}", "${desc}", "${status}")`)

}

modal_desc_text = document.getElementById('modal-desc-text')
modal_desc_info = document.getElementById('modal-desc-info')
new_description = document.getElementById('new-description')


function change_description(port, desc) {

    modal_desc_text.innerHTML = 'Укажите новое описание для порта ' + port
    $('#modal-desc-yes').attr('onclick', `set_description("${port}")`)

}

function set_description(port) {

    modal_desc_info.innerHTML = `
    <div class="spinner-border" role="status">
      <span class="visually-hidden">Loading...</span>
    </div>`
    $('button').prop('disabled', true);
    modal_desc_info.className = '';

    let data = {
        port: port,
        device_name: device_name_,
        description: new_description.value,
        csrfmiddlewaretoken: csrf_token
    }

    $.ajax( {
        url: "/device/port/set-description",
        type: 'POST',
        data: data,
        success: function( data ) {
            $('button').prop('disabled', false);
            if (data){
                modal_desc_info.innerHTML = data.info;
                modal_desc_info.className = "alert-" + data.status + " alert";
                port_description.html(data.description);

                if (data.max_length) {
                    new_description.maxLength = data.max_length;
                }

            }
        },
        error: function ( data ) {
            console.log(data)
            modal_desc_info.innerHTML = 'Неверное описание';
            $('button').prop('disabled', false);
        }
    } );
}