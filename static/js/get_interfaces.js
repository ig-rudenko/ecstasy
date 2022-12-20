/**
 * Он делает запрос AJAX к текущему URL-адресу и заменяет содержимое элемента `#interfaces-table` ответом.
 */
function get_interfaces() {
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
            // if (first){ document.getElementById('auto-update-interfaces').checked = false; }
            window.last_time = Date.now() / 1000

            window.tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
            window.tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
        },
    });

}

get_interfaces();
