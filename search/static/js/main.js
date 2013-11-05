$(document).ready(function(){
    // preload images
    /*
    var MEDIA_ROOT = '../img/';
    var preload = ['link_hover.png', 'star_hover.png'];
    for (var i = 0; i < preload.length; i++) {
        $('<img />').attr('src', MEDIA_ROOT + preload[i]);
    }
    */
    var inputs = document.getElementsByTagName('input');
    for (var i = 0; i < inputs.length; i++) {
        inputs[i].autocomplete = "off";
    }

    $('.search input').focus();
    $('button.add-gif').click(function() {
        $('.modal-mask, #add-gif').toggle(0, function(){
            if ($('#add-gif').is(':visible')) { 
                var add_gif = $('#add-gif input');
                add_gif.focus();
                add_gif.on('input', function(){
                    alert(add_gif.val());
                });
            } else {
                $('.search input').focus();
            }
        });
        $('.modal-mask').click(function() {
            $('.modal-mask, #add-gif').hide();
            $('.search input').focus();
        });
    });
});

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function ajaxPost(params, endpoint, callback_success) {
    params.csrfmiddlewaretoken = getCookie('csrftoken');
    $.ajax({
        type: "POST",
        url: endpoint,
        data: params,
        success: callback_success,
        error: function(xhr, textStatus, errorThrown) {
            alert("Please report this error: "+errorThrown+xhr.status+xhr.responseText);
        }
    }); 
}
