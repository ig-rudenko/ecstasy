function get_session(mac, device_name, port){
    let data = {
        mac: mac,
        device: device_name,
        port: port,
        ajax: true
    }

    $.ajax({
        url: "/session",
        type: 'GET',
        data: data,
        success: function( data ) {
            console.log(data)
            $('#brases-data').html(data)
        }
    });
}