function get_interfaces() {

    $.ajax({
        url: window.location.href + '&ajax=1',
        type: 'GET',
        success: function( data ) {
            $('#interfaces-table').html(data.data)
            if (first){ document.getElementById('auto-update-interfaces').checked = false; }
            window.last_time = Date.now() / 1000

            window.tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
            window.tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
        },
    });

}

get_interfaces();
