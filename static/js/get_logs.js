$.ajax({
    url: "/device/"+$("name").html()+'/logs?ajax=1',
    type: 'GET',
    success: function( data ) {
        var re1 = new RegExp('\n', 'g');
        var re2 = new RegExp(' ', 'g');
        $('#logs').html(data.logs.replace(re2, '&nbsp;').replace(re1, '<br>'))
    }
});