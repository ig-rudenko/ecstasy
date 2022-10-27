let session_data = $('#brases-data')

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