/**
 * Он делает AJAX-запрос к тому же URL-адресу, что и текущая страница, но с добавленным параметром ajax=1.
 * Затем ответ используется для замены содержимого элемента `#interfaces-table`.
 */
let FIRST_REQUEST = true
function get_interfaces() {

    if ( document.getElementById('auto-update-interfaces').checked || FIRST_REQUEST) {
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
                if (FIRST_REQUEST){ get_device_info() }

                $('#interfaces-table').html(data.data)
                window.last_time = Date.now() / 1000

                window.tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
                window.tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

                FIRST_REQUEST = false

                setTimeout(get_interfaces, 4000);
            },
        });
    }
}

// ЗАПРОС ИНТЕРФЕЙСОВ
get_interfaces();
