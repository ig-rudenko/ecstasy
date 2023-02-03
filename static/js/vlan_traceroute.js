/**
 * Он загружает содержимое страницы /tools/ajax/vlantraceroute в div с включенным идентификаторомContent.
 */

const CSRF_TOKEN = $('input[name=csrfmiddlewaretoken]')[0].value

const LOADING_CIRCLE = `<div class="spinner-border" role="status"></div>`
const RUN_SCAN_BUTTON = `<svg style="cursor: pointer" onclick="run_vlans_scan()" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="white" class="bi bi-arrow-clockwise" viewBox="0 0 16 16">
                             <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"></path>
                             <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"></path>
                         </svg>`
const SCANNING_ERROR = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="white" class="bi bi-x-circle" viewBox="0 0 16 16">
                          <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                          <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
                        </svg>`

let SCANNING = false
const scan_block = document.getElementById("vlans-scan")

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
              if (status === "success" && response !== 'empty') {
                  $("#fullScreen").css('display', 'block');
                  network_map = document.getElementById('mynetwork').parentElement
                  network_map.style.height = '100%';
                  vlan_map.style.height = '500px';
              }
          }
      );
    });
}


function check_vlans_scan_status() {
    if (!SCANNING){
        $.ajax({
            data: {'csrfmiddlewaretoken': CSRF_TOKEN},
            type: 'post',
            url: '/tools/ajax/vlans-scan/check',
            success: function (response) {
                if (!response.scanning) {
                    scan_block.innerHTML = RUN_SCAN_BUTTON
                } else {
                    scan_block.innerHTML = LOADING_CIRCLE
                }
            },
            error: function (response) {
                scan_block.innerHTML = SCANNING_ERROR
            }
        });
    }
    setTimeout(check_vlans_scan_status, 5000);
}


function run_vlans_scan() {
    scan_block.innerHTML = LOADING_CIRCLE
    SCANNING = true

    $.ajax({
        data: {'csrfmiddlewaretoken': CSRF_TOKEN},
        type: 'post',
        url: '/tools/ajax/vlans-scan/run',
        success: function (response) {
            if(!response.task_id) {
                scan_block.innerHTML = SCANNING_ERROR
                SCANNING = false
            } else {
                scan_block.innerHTML = LOADING_CIRCLE
            }
        },
        error: function (response) {
            scan_block.innerHTML = SCANNING_ERROR
            SCANNING = false
        }
    })
}

$("#vlan").keyup(function(event) {
    if (event.keyCode === 13) {
        show_map();
    }
});

let vlan_map = document.getElementById('includedContent');
let collapse_screen = document.getElementById('collapseScreen');
let network_map

// Кнопка развернуть на весь экран
document.getElementById("fullScreenButton").onclick = function show_full_screen () {
    vlan_map.classList.add('fullScreen');
    vlan_map.style.height = '100%';
    network_map.style.border = '0'
    collapse_screen.style.display = 'block';
}

// Кнопка свернуть
document.getElementById("collapseScreenButton").onclick = function show_collapse_screen () {
    vlan_map.classList.remove('fullScreen');
    vlan_map.style.height = '500px';
    network_map.style.border = '1px solid lightgray';
    collapse_screen.style.display = 'none';
}