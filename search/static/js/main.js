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
                    if ($(this).val().length > 0)
                        console.log("detected a non-zero input change");
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
    var re = /\s*\/?(?:fig\.)?([a-zA-Z0-9]+)(?:\/|$)/;
    var match = reverse(string).match(re);
    /* traverse the string backwards, return the result forwards.
     * doing this because all the significant data we care about is at the end,
     * and it's much easier to write a regex to match *until* x rather than try
     * to account for all the stuff we want to ignore traversing forwards. */
    if (match) {
        var filename = reverse(match[1]);
        console.log("Found match: " + filename);
        testImage(filename, addGifCallback);
    } else badUrl("Whoops! That's not a vaild imgur image URL.");
}

function addGifCallback(filename, url, message) {
    if (message === "error" || message === "timeout") {
        badGif("Whoops! That's not a vaild imgur image URL.");
    } else { goodUrl(filename) }
}

function badGif(message) {
    $('#add-gif .error').text(message);
    $('#add-gif input').select();
}

function goodUrl(filename) {
    console.log("ajax posting with filename: " + filename);
    ajaxPost(
        {'filename': filename},
        "/api/gif-check/",
        goodGif);
}

function goodGif(response) {
    if (response.result) {
        if (response.error === "AlreadyExistsError")
            badGif("This GIF is already in GIFdatabase. Try another!");
        else if (response.error === "InvalidFileError")
            badGif("Whoops! That's not an animated GIF.");
        else
            alert("Oh noes! Something went wrong. Please report this error: \n" + response.error + ": " + response.message);
    } else {
        $('#add-gif, .modal-mask').hide();
        var aside_content = "<input class='tag-add-new' maxlength='"+context.TAG_MAX_LEN+"'/><button class='disabled medium save'>Save</button>"
        $.slimbox(response.url, aside_content, {is_new: true});
    }
}

function testImage(filename, callback, timeout) {
    var url = "http://i.imgur.com/" + filename + ".gif";
    timeout = timeout || 5000;
    var timedOut = false, timer;
    var img = new Image();
    img.onerror = img.onabort = function() {
        if (!timedOut) {
            clearTimeout(timer);
            callback(filename, "error");
        }
    };
    img.onload = function() {
        if (!timedOut) {
            clearTimeout(timer);
            callback(filename, "success");
        }
    };
    img.src = url;
    timer = setTimeout(function() {
        timedOut = true;
        callback(filename, "timeout");
    }, timeout); 
}


/* utility functions */

function reverse(s){
    return s.split("").reverse().join("");
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
            alert("Oh noes! Something went wrong. Please report this error: \n"+errorThrown+xhr.status+xhr.responseText);
        }
    }); 
}
