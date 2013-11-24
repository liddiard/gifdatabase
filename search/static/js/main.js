$(document).ready(function(){
    /* turn autocomplete off for all inputs */
    var inputs = document.getElementsByTagName('input');
    for (var i = 0; i < inputs.length; i++) {
        inputs[i].autocomplete = "off";
    }

    colorScore();
    $('.search input').focus();

    $('.add-gif').click(addGifModal);

    $('.user-actions .user, .user-actions .star').tipsy({gravity: 'n'});
    $('#imgur-link').tipsy({gravity:'w'}).click(function(){ $('#add-gif input').focus() });
    $('.list-next').tipsy({gravity:'w'});

    if (context.login_result) {
        if (context.login_result === 1)
            loginNotification("error", "Your account is not currently active. Have you clicked the link in the activation email?");
        else
            loginNotification("error", "Invalid username or password.");
    }
});

function addGifModal() {
    $('.modal-mask, #add-gif').toggle(0, function(){
        if ($('#add-gif').is(':visible')) { 
            var add_gif = $('#add-gif input');
            add_gif.focus();
            add_gif.on('input', function(){
                if ($(this).val().length > 0) {
                    console.log("detected a non-zero input change");
                    add_gif.prop('disabled', true);
                    showGifFromUrl(add_gif.val());
                } else add_gif.prop('disabled', false);
            });
        } else {
            $('.search input').focus();
        }
    });
    $('.modal-mask').click(function() {
        $('.modal-mask, #add-gif').hide();
        $('.search input').focus();
    });
}

function showGifFromUrl(string) {
    var re = /\s*\/?(?:fig\.)?([a-zA-Z0-9]+)(?:\/|$)/;
    var match = reverse(string).match(re);
    /* traverse the string backwards, return the result forwards.
     * doing this because all the significant data we care about is at the end,
     * and it's much easier to write a regex to match *until* x rather than try
     * to account for all the stuff we want to ignore traversing forwards. */
    if (match) {
        add_gif_filename = reverse(match[1]);
        console.log("Found match: " + add_gif_filename);
        goodUrl(add_gif_filename);
    } else badUrl("Whoops! That's not a vaild imgur image URL.");
}

/* currently bypassed */
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
    var check_spinner = $('.lbLoading.check-gif');
    check_spinner_id = typeof check_spinner_id === 'undefined' ? animateSpinner(check_spinner, 22, 8) : check_spinner_id;
    check_spinner.show();
    ajaxPost(
        {'filename': filename},
        "/api/gif-check/",
        goodGif);
}

function goodGif(response) {
    $('.lbLoading.check-gif').hide();
    var add_gif_input = $('#add-gif input');
    add_gif_input.prop('disabled', false);
    if (response.result) {
        if (response.error === "AlreadyExistsError")
            badGif("Sorry, that GIF is already in GIFdatabase. Try another!");
        else if (response.error === "InvalidFileError")
            badGif("Whoops! That's not an animated GIF.");
        else
            alert("Oh no! Something went wrong. Please report this error: \n" + response.error + ": " + response.message);
    } else {
        add_gif_input.val('');
        $('#add-gif .error').text('');
        $('#add-gif, .modal-mask').hide();
        var aside_content = "<input class='tag-add-new' placeholder='+ add tags' maxlength='"+context.TAG_MAX_LEN+"'/><button class='disabled medium save'>Save</button><div class='lbLoading small save'></div>"
        $.slimbox(response.url, aside_content, {is_unsaved: true});
    }
}

/* currently bypassed */
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

function colorScore(score_elem) {
    function colorScoreElement(score_elem) {
        if (parseInt(score_elem.text()) < 0) {
            score_elem.addClass('negative');
        }
    }
    if (score_elem === undefined) {
        $('.score').each(function(){
            colorScoreElement($(this));
        });
    } else colorScoreElement(score_elem);
}

function loginNotification(type, message) {
    var banner = $('.login-required');
    banner.text(message);
    banner.addClass(type);
    banner.show();
}

function loginRequired(action) {
    if (context.user_is_authenticated)
        return false;
    else {
        var actions = {'tag_add': "add tags.",
                       'tag_vote': "vote on tags.",
                       'star': "star your favorite GIFs."};
        var nut = actions[action] || "do that.";
        var message = "Log in or create an account to " + nut;
        loginNotification("alert", message);
        $('form#login input:nth-child(2)').focus();
        return true;
    }
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
            alert("Oh no! Something went wrong. Please report this error: \n"+errorThrown+xhr.status+xhr.responseText);
        }
    }); 
}

function animateSpinner(spinner, size, steps) {
    var height = size * steps;
    var offset = 0;
    spinner.css('background-position-y', offset+'px');
    var interval_id = setInterval(function(){
        spinner.css('background-position-y', offset+'px');
        offset -= size;
        if (offset <= -height)
            offset = 0;
    }, 100);
    return interval_id;
}

