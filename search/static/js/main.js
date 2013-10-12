$(document).ready(function(){
	$('.tag').hover(
		function(){
			$(this).parent().addClass('tag-confirm');},
		function(){
			$(this).parent().removeClass('tag-confirm');}
	);
});
