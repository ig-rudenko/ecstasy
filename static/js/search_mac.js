function start_mac_search (){
    let macAddress = $('#mac').val().replace(/[^A-Za-z\d]/g,"").substring(0,12);

    if (macAddress.length === 12) {
        $('#info').removeClass('block_visible').addClass('block_hide')
        $('#zabbix').removeClass('block_visible').addClass('block_hide')
        $('#vendor').removeClass('block_visible').addClass('block_hide')
        $('#mac-element').addClass('load_border')
        get_vendor(macAddress)
        get_from_arp(macAddress)

    } else {
        $('#result').removeClass('block_visible').addClass('block_hide')
        $('#mac-element').removeClass('load_border')
    }
}

$(function (){
    $('#mac').on('input', start_mac_search)
})

function get_vendor(macAddress) {
    $.ajax({
        type: 'get',
        url: '/tools/ajax/mac_vendor/' + macAddress,
        success: function (response) {
            $('#vendor_name').html(response.vendor)
            $('#vendor').removeClass('block_hide').addClass('block_visible')
            $('#result').removeClass('block_hide').addClass('block_visible')
        }
    })
}

function get_from_arp(macAddress) {
    $.ajax({
        type: 'get',
        url: '/tools/ajax/mac_info/' + macAddress,
        success: function (response) {
            if (response.info.length) {
                $('#info_ip').html(response.info[0])
                // $('#info_vlan').html(response.info[0][1])

            } else {
                $('#info_ip').html('В нашей сети MAC не найден')
                $('#info_vlan').html('')
            }

            $('#mac-element').removeClass('load_border')
            $('#info').removeClass('block_hide').addClass('block_visible')
            $('#result').removeClass('block_hide').addClass('block_visible')

            if (response.zabbix.length) {
                let zabbix_info = ''
                for ( let i=0; i<response.zabbix.length; i++ ) {
                    zabbix_info += '<p><a target="_blank" href="http://10.100.0.50/zabbix/hostinventories.php?hostid='+response.zabbix[i][1]
                        +'">> '+response.zabbix[i][0]+' <</a></p>'
                }
                //console.log(zabbix_info)
                $('#zabbix_host_name').html(zabbix_info).css({'top': 0})
                $('#zabbix').css({'height': (35+52*response.zabbix.length)+'px'}).removeClass('block_hide').addClass('block_visible')
            } else {
                $('#zabbix').removeClass('block_visible').addClass('block_hide')
            }
        },
        error: function (resp) {
            console.log(resp)
            $('#mac-element').removeClass('load_border')
        }
    })
}
