/**
 * Он принимает строку и тип поиска, а затем отправляет запрос AJAX на сервер.
 * @param find_type - Тип выполняемого поиска.
 */
function start_find (find_type) {
    let find_str = document.getElementById('find_str').value;
    if (!find_str){return}

    let circle_load = `
    <div class="text-center">
        <img height="200px" src="/static/img/load_desc.gif">
    </div>`;

    let descriptions = $('#content-point');

    descriptions.html(circle_load);
    $('#search-menu').prop('disabled', true);
    $('#find_str').prop('disabled', true);

    /* Отправка ajax-запроса на сервер. */
    $.ajax({
        data: {
            'string': find_str,
            'type': find_type
        },
        type: 'get',
        url: '/tools/ajax/find',
        success: function (response) {
            descriptions.html(response);
            $('#search-menu').prop('disabled', false);
            $('#find_str').prop('disabled', false);
        },
        error: function (response) {
            descriptions.html(response);
        }
    });
}