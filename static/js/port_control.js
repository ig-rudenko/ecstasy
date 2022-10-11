function reload_port(port, desc, status) {
    let data = {
            port: port,
            device: $("name").html(),
            desc: desc,
            status: status,
            csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]')[0].value
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
        }
    } );
}

modal_text = document.getElementById('modal-text')
modal_port_desc = document.getElementById('modal-port-desc')
modal_ok = document.getElementById('modal-yes')

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

    $('#modal-yes').attr('onclick', `reload_port("${port}", "${desc}", "${status}")`)

}