/* not currently working */

$(document).ready(function(){
    $('#login[type="submit"]').click(function(event){
        event.preventDefault();
        ajaxLogin($(this));
    });
});

function ajaxLogin(element) {
    $.post("/login/", $(element).serialize()
        .done(function(data), alert(data));
}