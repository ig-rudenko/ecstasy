function get_interfaces(first=false) {

    if ( document.getElementById('auto-update-interfaces').checked || first) {
        let request_url = window.location.href

        if (window.location.href.includes('?')) {
            request_url += '&ajax=1'
        } else {
            request_url += '?ajax=1'
        }

        $.ajax({
            url: request_url,
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
    interface_timer()

}

    // Повторный сбор интерфейсов через 20 секунд
    function interface_timer() {
        setTimeout(get_interfaces, 20000);
    }

// ЗАПРОС ИНТЕРФЕЙСОВ
get_interfaces(true);
