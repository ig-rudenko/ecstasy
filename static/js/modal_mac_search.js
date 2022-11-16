let vendor = document.getElementById('modal-mac-vendor')
let mac = document.getElementById('modal-mac-str')

let result_div = document.getElementById('modal-mac-result')

function get_vendor(mac_value) {
    $.ajax({
        type: 'get',
        url: '/tools/ajax/mac_vendor/' + mac_value,
        success: function (response) {
            vendor.innerHTML = response.vendor;
        }
    })
}

function get_info_wtf(mac_value) {
    $.ajax({
        type: 'get',
        url: '/tools/ajax/ip-mac-info/' + mac_value,
        success: function (response) {
            result_div.innerHTML = response
        },
        error: function (response) {
            console.log(response)
        }
    });
}


function start_search_mac(mac_value) {
    mac.innerHTML = mac_value
    vendor.innerHTML = ''
    result_div.innerHTML = `<div class="spinner-border" role="status">
    <span class="visually-hidden">Loading...</span>
    </div>`
    get_vendor(mac_value)
    get_info_wtf(mac_value)
}