let vendor = document.getElementById('modal-mac-vendor')
let mac = document.getElementById('modal-mac-str')

let result_div = document.getElementById('modal-mac-result')

function get_vendor() {
    $.ajax({
        type: 'get',
        url: '/tools/ajax/mac_vendor/' + mac.innerHTML,
        success: function (response) {
            console.log(response)
            vendor.innerHTML = response.vendor;
        }
    })
}

function get_mac_info() {
    $.ajax({
        type: 'get',
        url: '/tools/ajax/mac_info/' + mac.innerHTML,
        success: function (response) {
            console.log(response)
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
    get_vendor()
    get_mac_info()
}