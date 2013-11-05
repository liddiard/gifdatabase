$(document).ready(function(){
    /* turn autocomplete off for all inputs */
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
                    showGifFromUrl(add_gif.val());
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

function showGifFromUrl(string) {
    var re = /[^(http:\/\/i.imgur.com/gallery)][a-zA-Z0-9]+[^(\.gif)]/;
    var match = string.match(re);
    if (match) {
        var url = "http://i.imgur.com/" + match[0] + ".gif";
        testImage(url, addGifCallback);
    }
}

function addGifCallback(url, message) {
    if (message === "error" || message === "timeout") {
        badUrl();
    } else { goodUrl() }

    function badUrl() {
        alert("your url is bad and your should feel bad.");
    }

    function goodUrl() {
        alert("that's one sexy url");
    }
}

function testImage(url, callback, timeout) {
    timeout = timeout || 5000;
    var timedOut = false, timer;
    var img = new Image();
    img.onerror = img.onabort = function() {
        if (!timedOut) {
            clearTimeout(timer);
            callback(url, "error");
        }
    };
    img.onload = function() {
        if (!timedOut) {
            clearTimeout(timer);
            callback(url, "success");
        }
    };
    img.src = url;
    timer = setTimeout(function() {
        timedOut = true;
        callback(url, "timeout");
    }, timeout); 
}

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
