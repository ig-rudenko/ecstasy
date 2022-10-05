function show_map() {
    let vlan = document.getElementById('vlan').value
    let empty_ports = document.getElementById('empty-ports').checked
    let only_admin_up = document.getElementById('only-admin-up').checked
    document.getElementById('load_circle').style.display = 'block'
    if (!vlan){document.getElementById('load_circle').style.display = 'none';return}

    $.ajax({
        data: {'vlan': vlan},
        type: 'get',
        url: '/tools/ajax/vlan_desc',
        success: function (resp) {
            console.log(resp)
            if (resp.vlan_desc) {
                document.getElementById('vlan-desc').innerText = resp.vlan_desc
                document.getElementById('vlan-desc').style.padding = "8px"
            } else {
                document.getElementById('vlan-desc').innerText = ''
                document.getElementById('vlan-desc').style.padding = "0"
            }
        },
        error: function (resp) {
            console.log('error', resp)
            document.getElementById('vlan-desc').innerText = ''
            document.getElementById('vlan-desc').style.padding = "0"
        }
    })

    $(function(){
      $("#includedContent").load(
          '/tools/ajax/vlantraceroute?vlan=' + vlan + '&ep=' + empty_ports + '&ad=' + only_admin_up,
          function (response, status) {
              if (status === "success") {
                  document.getElementById('load_circle').style.display = 'none'
              }
          }
      );
    });
    document.getElementById('includedContent').style.height = "111%"
}

$("#vlan").keyup(function(event) {
    if (event.keyCode === 13) {
        show_map();
    }
});