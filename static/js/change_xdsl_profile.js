let profile_load_div = $('#profile-load')
let profile_status_div = $('#profile-status')

function change_port_profile(profile_index, profile_name) {

    $('button').prop('disabled', true);
    profile_load_div.prop('hidden', false);
    profile_status_div.prop('hidden', true)

    let data = {
        port: device_port,
        device_name: device_name,
        index: profile_index,
        csrfmiddlewaretoken: csrf_token
    }
    console.log(data)

    $.ajax({
        url: "/device/port/change-profile",
        type: 'POST',
        data: data,
        success: function( data ) {
            console.log(data)
            $('button').prop('disabled', false);
            $('#profile-name').html(profile_name)
            profile_load_div.prop('hidden', true);
            profile_status_div.prop('hidden', false)
                .removeClass('alert-danger')
                .addClass('alert-success')
                .html('Профиль был изменен на ' + profile_name)

        },
        error: function (data){
            console.log(data)
            $('button').prop('disabled', false);
            profile_load_div.prop('hidden', true);
            profile_status_div.prop('hidden', false)
                .removeClass('alert-success')
                .addClass('alert-danger')
                .html('Ошибка ' + data)
        }
    });
}