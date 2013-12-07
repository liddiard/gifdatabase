$(document).ready(function(){
    /* turn autocomplete off for all inputs */
    var inputs = document.getElementsByTagName('input');
    for (var i = 0; i < inputs.length; i++) {
        inputs[i].autocomplete = "off";
    }

    colorScore();
    $('.search input').focus();

    $('button.add-gif').click(addGifModal);

    $('.user-actions .user, .user-actions .star').tipsy({gravity: 'n'});
    $('#imgur-link').tipsy({gravity:'w'}).click(function(){ $('#add-gif input').focus() });
    $('.list-next, .account-preferences').tipsy({gravity:'w'});

    if (context.login_result) {
        if (context.login_result === 1)
            bannerNotification("error", "Your account is not active. Have you clicked the link in the verification email?");
        else
            bannerNotification("error", "Invalid username or password. Forgot your password? You can <a class='highlight' href='http://"+document.domain+":"+location.port+"/account/password/reset/'>reset it</a>.");
    }
});

function addGifModal() {
    $('.modal-mask, #add-gif').toggle(0, function(){
        var add_gif = $('#add-gif input');
        if ($('#add-gif').is(':visible')) { 
            add_gif.on('input', function(){ gifInputChange(add_gif, ajaxCheckGif) });
            add_gif.focus();
        } else {
            add_gif.unbind('input');
            $('.modal-mask').unbind('click');
            $('.search input').focus();
        }
    });
    $('.modal-mask').click(function() {
        $('.modal-mask, #add-gif').hide();
        $(this).unbind('click');
        $('.search input').focus();
    });
}

function gifInputChange(elem, callback_action) {
    console.log(arguments);
    if (elem.val().length > 0) {
        console.log("detected a non-zero input change");
        elem.prop('disabled', true);
        showGifFromUrl(elem.val(), callback_action);
    } else elem.prop('disabled', false);
}

function showGifFromUrl(string, callback_action) {
    var re = /\s*\/?(?:fig\.)?([a-zA-Z0-9]+)(?:\/|$)/;
    var match = reverse(string).match(re);
    /* traverse the string backwards, return the result forwards.
     * doing this because all the significant data we care about is at the end,
     * and it's much easier to write a regex to match *until* x rather than try
     * to account for all the stuff we want to ignore traversing forwards. */
    if (match) {
        add_gif_filename = reverse(match[1]);
        console.log("Found match: " + add_gif_filename);
        goodUrl(add_gif_filename, callback_action);
    } else badGif("Whoops! That's not a vaild imgur image URL.");
}

function goodUrl(filename, callback_action) {
    console.log("ajax posting with filename: " + filename);
    var check_spinner = $('.lbLoading.check-gif');
    check_spinner_id = typeof check_spinner_id === 'undefined' ? animateSpinner(check_spinner, 22, 8) : check_spinner_id;
    check_spinner.show();
    callback_action(filename);
}

function ajaxCheckGif(filename) {
    ajaxPost(
        {'filename': filename},
        "/api/gif-check/",
        goodGif);
}

function badGif(message) {
    var input = $('.modal input:visible');
    $('.modal:visible .error').text(message).stop().css("opacity", "1").fadeTo(12000, 0.6);
    input.prop('disabled', false);
    input.select();
}

function goodGif(response) {
    $('.lbLoading.check-gif').hide();
    var input = $('.modal input:visible');
    if (response.result) {
        if (response.error === "AlreadyExistsError")
            badGif("Sorry, that GIF is already in GIFdatabase. Try another!");
        else if (response.error === "InvalidFileError")
            badGif("Whoops! That's not an animated GIF.");
        else
            alert("Oh no! Something went wrong. Please report this error: \n" + response.error + ": " + response.message);
    } else {
        input.val('');
        $('.modal:visible .error').text('');
        $('.modal, .modal-mask').hide();
        var aside_content = "<input class='tag-add-new' placeholder='+ add tags' maxlength='"+context.TAG_MAX_LEN+"'/><button class='disabled medium save'>Save</button><div class='lbLoading small save'></div>"
        $.slimbox(response.url, aside_content, {is_unsaved: true});
    }
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

function bannerNotification(type, message) {
    var banner = $('.notification');
    banner.html(message);
    banner.addClass(type);
    banner.show();
}

function loginRequired(action) {
    var actions = {'tag_add': "add tags",
                   'tag_vote': "vote on tags",
                   'star': "star your favorite GIFs"};
    var nut = actions[action] || "do that";
    if (context.user_is_authenticated) {
        if (context.user_can_add)
            var message = "You can't currently "+nut+" because your score is low. Add some GIFs to improve your score!";
        else
            var message = "You can't "+nut+" because your score is low."
        if (action === 'tag_add' || action === 'tag_vote') {
            if (context.user_can_tag)
                return false;
            else {
                bannerNotification("error", message);
                return true;
            }
        }
        else return false;
    }
    else {
        var message = "Log in or create an account to "+nut+".";
        bannerNotification("alert", message);
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

