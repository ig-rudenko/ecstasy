var SEARCH = true;
var count_dict = new Map();


hashCode = s => String(s.split('').reduce((a,b)=>{a=((a<<5)-a)+b.charCodeAt(0);return a&a},0))

function stop_search() {
    SEARCH = false
    document.getElementById('stop-btn').style.display = 'none'
    document.getElementById('load_circle').style.display = 'none'
    document.getElementById('content-point').innerHTML = 'Поиск завершен'
}


function start_search(search_string, search_type) {
    let search_type_ = hashCode(search_type)
    let search_string_ = hashCode(search_string)
    count_dict.set(search_string_+search_type_, 0)
    SEARCH = true
    if (search_type === 'string') {
        var label = 'СТРОКИ: '
    } else {
        label = 'ПО РЕГУЛЯРНОМУ ВЫРАЖЕНИЮ: '
    }
    document.getElementById('load_circle').style.display = 'block'
    document.getElementById('stop-btn').style.display = ''
    document.getElementById('content-point').innerHTML = 'Идет поиск, пожалуйста, подождите...'
    $('#content-point').after(`
    <div id='data_div${search_string_+search_type_}' style="text-align: center; margin: 20px">
        <span style="text-align: center">ПОИСК ${label}</span><span style="color: #006b1b"> ${search_string}</span>
        <span id=percent-${search_string_+search_type_}></span>
        <table id='data_table${search_string_+search_type_}' style="margin: auto; display: none">
            <th>Узел сети</th><th>Интерфейс</th><th>Описание</th><th>Время сохранения</th>
            <tr id="end-table-head${search_string_+search_type_}"></tr>
        </table>
    </div>`)
}


function add_row(data, add_after, search_id){
    add_after = '#'+add_after
    for (var i = 0; i < data.length; i++) {
        var tr_id = hashCode(data[0].Device)
        if (i === 0) tr_id = hashCode(data[0].Device)+'-last'

        $(add_after).after(
            `<tr id="d${tr_id}"><td style="color: #337AB7">
<a target="_blank" href="{{ zabbix_url }}/zabbix.php?action=host.view&filter_name=${data[i].Device}&filter_ip=&filter_dns=&filter_port=&filter_status=-1&filter_evaltype=0&filter_tags%5B0%5D%5Btag%5D=&filter_tags%5B0%5D%5Boperator%5D=0&filter_tags%5B0%5D%5Bvalue%5D=&filter_maintenance_status=1&filter_show_suppressed=0&filter_set=1">
            ${data[i].Device}</a></td><td>
            ${data[i].Interface}</td><td>
            ${data[i].Description}</td><td style="color: green">
            ${data[i].SavedTime}</td></tr>`
        )
        count_dict.set(search_id, count_dict.get(search_id)+1)
    }
}


function start_find (find_type) {
    let find_str = document.getElementById('find_str').value
    if (!find_str){return}
    start_search(find_str, find_type)
    $.ajax({
        data: {
            'string': find_str,
            'type': find_type
        },
        type: 'get',
        url: '/tools/ajax/find',
        success: function (response) {
            console.log(response)
            if (response.data.length && SEARCH) {

                // Добавляем первую строчку в таблицу
                add_row(
                    response.data,
                    'end-table-head'+hashCode(find_str)+hashCode(find_type),
                    hashCode(find_str)+hashCode(find_type)
                )

                document.getElementById('data_table'+hashCode(find_str)+hashCode(find_type)).style.display = ''

                document.getElementById('percent-'+hashCode(find_str)+hashCode(find_type)).innerHTML = response.data[0].percent
                    + ' Найдено: ' + count_dict.get(hashCode(find_str)+hashCode(find_type))

                stop_search()

            } else {
                stop_search()
                document.getElementById('content-point').innerHTML = 'Ничего не найдено'
                document.getElementById('data_div'+hashCode(find_str)+hashCode(find_type)).style.display = 'none'
                }
        },
        error: function (response) {
            console.log(response)
        }
    }
    )
}