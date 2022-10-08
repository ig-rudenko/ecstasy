function show_map() {
    let vlan = document.getElementById('vlan').value;
    let empty_ports = document.getElementById('empty-ports').checked;
    let only_admin_up = document.getElementById('only-admin-up').checked;

    let vlan_desc = $("#vlan_desc");

    $("#includedContent").html(`
    <div class="spinner-border text-light" role="status">
    </div>`)

    vlan_desc.html(`
    <div class="spinner-border" role="status">
      <span class="visually-hidden">Loading...</span>
    </div>`);

    $.ajax({
        data: {'vlan': vlan},
        type: 'get',
        url: '/tools/ajax/vlan_desc',
        success: function (resp) {
            if (resp.vlan_desc) {
                vlan_desc.html(resp.vlan_desc);
            } else {
                vlan_desc.html('');
            }
        },
        error: function (resp) {
            console.log(resp);
            vlan_desc.html('');
        }
    })

    $(function(){
      $("#includedContent").load(
          '/tools/ajax/vlantraceroute?vlan=' + vlan + '&ep=' + empty_ports + '&ad=' + only_admin_up,
          function (response, status) {
              if (status === "success") {
                  $("#fullScreen").css('display', 'block');
                  network_map = document.getElementById('mynetwork')
                  network_map.style.borderRadius = '20px'
              }
          }
      );
    });
}

$("#vlan").keyup(function(event) {
    if (event.keyCode === 13) {
        show_map();
    }
});

let vlan_map = document.getElementById('includedContent');
let collapse_screen = document.getElementById('collapseScreen');
let network_map

// развернуть
document.getElementById("fullScreenButton").onclick = function show_full_screen () {
    vlan_map.classList.add('fullScreen');
    vlan_map.style.height = '100%';
    network_map.style.border = '0'
    collapse_screen.style.display = 'block';
}

// свернуть
document.getElementById("collapseScreenButton").onclick = function show_collapse_screen () {
    vlan_map.classList.remove('fullScreen');
    vlan_map.style.height = '500px';
    network_map.style.border = '1px solid lightgray';
    collapse_screen.style.display = 'none';
}