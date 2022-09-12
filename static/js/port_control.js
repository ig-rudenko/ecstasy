function reload_port(port, desc, status) {
    if (confirm('Слыш!\nУверен(а), что хочешь ' + status + ' порт:\n"' + desc + '"?')) {
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
}
