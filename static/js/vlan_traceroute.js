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
            vlan_desc.html('');
        }
    })

    $(function(){
      $("#includedContent").load(
          '/tools/ajax/vlantraceroute?vlan=' + vlan + '&ep=' + empty_ports + '&ad=' + only_admin_up,
          function (response, status) {
              if (status === "success") {
                  document.getElementById('load_circle').style.display = 'none';
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