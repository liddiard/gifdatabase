/*!
	Taglight - an extension of:
    Slimbox v2.05 - The ultimate lightweight Lightbox clone for jQuery
	(c) 2007-2013 Christophe Beyls <http://www.digitalia.be>
	MIT-style license.
*/

CAPTION_WIDTH = 220; //this makes me cry a little
votes = {};

(function($) {

	// Global variables, accessible to Slimbox only
	var win = $(window), options, images, activeImage = -1, activeURL, prevImage, nextImage, compatibleOverlay, middle, centerWidth, centerHeight,
		ie6 = !window.XMLHttpRequest, hiddenElements = [], documentElement = document.documentElement,

	// Preload images
	preload = {}, preloadPrev = new Image(), preloadNext = new Image(),

	// DOM elements
	overlay, center, image, sizer, prevLink, nextLink, topContainer, bottomContainer, aside, bottom, caption, number;

	/*
		Initialization
	*/

	$(function() {
		// Append the Slimbox HTML code at the bottom of the document
		$("body").append(
			$([
				overlay = $('<div id="lbOverlay" />').click(close)[0],
				center = $('<div id="lbCenter" />')[0],
                topContainer = $('<div id="lbTopContainer" />')[0],
                bottomContainer = $('<div id="lbBottomContainer" />')[0],
				aside = $('<div id="lbAside" />')[0]
			]).css("display", "none")
		);

		image = $('<div id="lbImage" />').appendTo(center).append(
			sizer = $('<div style="position: relative;" />').append([
				prevLink = $('<a id="lbPrevLink" href="#" />').click(previous)[0],
				nextLink = $('<a id="lbNextLink" href="#" />').click(next)[0]
			])[0]
		)[0];

		bottom = $('<div id="lbBottom" />').appendTo(aside).append([
			$('<a id="lbCloseLink" href="#" />').click(close)[0],
			caption = $('<div id="lbCaption" />')[0],
			number = $('<div id="lbNumber" />')[0],
			$('<div style="clear: both;" />')[0]
		])[0];
	});


	/*
		API
	*/

	// Open Slimbox with the specified parameters
	$.slimbox = function(_images, startImage, _options) {
		options = $.extend({
            is_new: false,            // Is the gif being created, or are we just viewing it? (user-added)
			loop: false,				// Allows to navigate between first and last images
			overlayOpacity: 0.8,			// 1 is opaque, 0 is completely transparent (change the color in the CSS file)
			overlayFadeDuration: 0,		// Duration of the overlay fade-in and fade-out animations (in milliseconds)
			resizeDuration: 1,			// Duration of each of the box resize animations (in milliseconds)
			resizeEasing: "swing",			// "swing" is jQuery's default easing
			initialWidth: 250,			// Initial width of the box (in pixels)
			initialHeight: 250,			// Initial height of the box (in pixels)
			imageFadeDuration: 0,			// Duration of the image fade-in animation (in milliseconds)
			captionAnimationDuration: 0,		// Duration of the caption animation (in milliseconds)
			counterText: false, // "gif {x} of {y}",	// Translate or change as you wish, or set it to false to disable counter text for image groups
			closeKeys: [27],		// Array of keycodes to close Slimbox, default: Esc (27), 'x' (88), 'c' (67)
			previousKeys: [37],			// Array of keycodes to navigate to the previous image, default: Left arrow (37), 'p' (80)
			nextKeys: [39]			// Array of keycodes to navigate to the next image, default: Right arrow (39), 'n' (78)
		}, _options);

		// The function is called for a single image, with URL and Title as first two arguments
		if (typeof _images == "string") {
			_images = [[_images, startImage]];
			startImage = 0;
		}

		middle = win.scrollTop() + (win.height() / 2);
		centerWidth = options.initialWidth;
		centerHeight = options.initialHeight;
		$(center).css({top: Math.max(0, middle - (centerHeight / 2)), width: centerWidth, height: centerHeight, marginLeft: -centerWidth/2}).show();
		compatibleOverlay = ie6 || (overlay.currentStyle && (overlay.currentStyle.position != "fixed"));
		if (compatibleOverlay) overlay.style.position = "absolute";
		$(overlay).css("opacity", options.overlayOpacity).fadeIn(options.overlayFadeDuration);
		position();
		setup(1);

		images = _images;
		options.loop = options.loop && (images.length > 1);
		return changeImage(startImage);
	};

	/*
		options:	Optional options object, see jQuery.slimbox()
		linkMapper:	Optional function taking a link DOM element and an index as arguments and returning an array containing 2 elements:
				the image URL and the image caption (may contain HTML)
		linksFilter:	Optional function taking a link DOM element and an index as arguments and returning true if the element is part of
				the image collection that will be shown on click, false if not. "this" refers to the element that was clicked.
				This function must always return true when the DOM element argument is "this".
	*/
	$.fn.slimbox = function(_options, linkMapper, linksFilter) {
		linkMapper = linkMapper || function(el) {
			return [el.href, $(el).find('.aside-data').html(),
                    $(el).find('.top-data').html(), $(el).find('.bottom-data').html()];
		};

		linksFilter = linksFilter || function() {
			return true;
		};

		var links = this;

		return links.unbind("click").click(function() {
			// Build the list of images that will be displayed
			var link = this, startIndex = 0, filteredLinks, i = 0, length;
			filteredLinks = $.grep(links, function(el, i) {
				return linksFilter.call(link, el, i);
			});

			// We cannot use jQuery.map() because it flattens the returned array
			for (length = filteredLinks.length; i < length; ++i) {
				if (filteredLinks[i] == link) startIndex = i;
				filteredLinks[i] = linkMapper(filteredLinks[i], i);
			}

			return $.slimbox(filteredLinks, startIndex, _options);
		});
	};


	/*
		Internal functions
	*/

	function position() {
		var l = win.scrollLeft(), w = win.width();
		$([center, aside, topContainer, bottomContainer]).css("left", l + (w / 2));
		if (compatibleOverlay) $(overlay).css({left: l, top: win.scrollTop(), width: w, height: win.height()});
	}

	function setup(open) {
		if (open) {
			$("object").add(ie6 ? "select" : "embed").each(function(index, el) {
				hiddenElements[index] = [el, el.style.visibility];
				el.style.visibility = "hidden";
			});
		} else {
			$.each(hiddenElements, function(index, el) {
				el[0].style.visibility = el[1];
			});
			hiddenElements = [];
		}
		var fn = open ? "bind" : "unbind";
		win[fn]("scroll resize", position);
		$(document)[fn]("keydown", keyDown);
	}

	function keyDown(event) {
		var code = event.which, fn = $.inArray;
		// Prevent default keyboard action (like navigating inside the page)
		return (fn(code, options.closeKeys) >= 0) ? close()
			: (fn(code, options.nextKeys) >= 0) ? next()
			: (fn(code, options.previousKeys) >= 0) ? previous()
			: null;
	}

	function previous() {
		return changeImage(prevImage);
	}

	function next() {
		return changeImage(nextImage);
	}

	function changeImage(imageIndex) {
		if (imageIndex >= 0) {
			activeImage = imageIndex;
			activeURL = images[activeImage][0];
			prevImage = (activeImage || (options.loop ? images.length : 0)) - 1;
			nextImage = ((activeImage + 1) % images.length) || (options.loop ? 0 : -1);

			stop();
			center.className = "lbLoading";

			preload = new Image();
			preload.onload = animateBox;
			preload.src = activeURL;
		}

		return false;
	}

	function animateBox() {
		center.className = "";
		$(image).css({backgroundImage: "url(" + activeURL + ")", visibility: "hidden", display: ""});
		$(sizer).width(preload.width);
		$([sizer, prevLink, nextLink]).height(preload.height);

		$(caption).html(images[activeImage][1] || "");
        $(topContainer).html(images[activeImage][2] || "");
        $(bottomContainer).html(images[activeImage][3] || "");
		$(number).html((((images.length > 1) && options.counterText) || "").replace(/{x}/, activeImage + 1).replace(/{y}/, images.length));

		if (prevImage >= 0) preloadPrev.src = images[prevImage][0];
		if (nextImage >= 0) preloadNext.src = images[nextImage][0];

		centerWidth = image.offsetWidth;
		centerHeight = image.offsetHeight;
		var top = Math.max(0, middle - (centerHeight / 2));
		if (center.offsetHeight != centerHeight) {
			$(center).animate({height: centerHeight, top: top}, options.resizeDuration, options.resizeEasing);
		}
		if (center.offsetWidth != centerWidth) {
			$(center).animate({width: centerWidth, marginLeft: -centerWidth/2}, options.resizeDuration, options.resizeEasing);
		}
		$(center).queue(function() {
            $([topContainer, bottomContainer]).css({width: centerWidth, marginLeft: -centerWidth/2, visibility: "hidden", display: ""});
            $(topContainer).css("top", top - 22); // TODO: number shouldn't be hardcoded
            $(bottomContainer).css("top", top + centerHeight);
			$(aside).css({width: CAPTION_WIDTH, top: top, marginLeft: centerWidth/2, visibility: "hidden", display: ""});
			$(image).css({display: "none", visibility: "", opacity: ""}).fadeIn(options.imageFadeDuration, animateCaption);
		});
	}

	function animateCaption() {
        
        /* have we already voted on this tag? color tags accordingly. */
        function ajaxGetTagVotes() {
            $('.tag').each(function(){
                var tag_id = $(this).attr('data-tag');
                ajaxPost({tag: tag_id}, "/api/tagvote-get/", ajaxInterpretTagVote);
            });
        }

        function ajaxInterpretTagVote(response) {
            var tag = response.tag;
            var v = response.vote;
            elem = $('.tag[data-tag='+tag+']');
            if (v !== 0) {
                if (v === 1) {
                    votes[tag] = true;
                    elem.addClass("tag-confirmed");
                }
                else if (v === -1) {
                    votes[tag] = false;
                    elem.addClass("tag-denied");
                }
                else
                    console.error("GetTagVoteError: server did not return a valid TagVote");
            }
        }

        ajaxGetTagVotes();

        function ajaxInterpretStar(response) {
            if (response.star === 1)
                $('#lbTopContainer .star').addClass('selected');
        }

        ajaxGetStar($('#lbTopContainer .star'));

		if (prevImage >= 0) $(prevLink).show();
		if (nextImage >= 0) $(nextLink).show();
		$(bottom).css("marginTop", -bottom.offsetHeight).animate({marginTop: 0}, options.captionAnimationDuration);
		aside.style.visibility = topContainer.style.visibility = bottomContainer.style.visibility = "";
       
        function toggleParentOnHover(selector, cls) {
            $(selector).hover(
                function(){
                    $(this).parent().addClass(cls);},
                function(){
                    $(this).parent().removeClass(cls);}
            );
        }

        function toggleClassOnHover(selector, cls) {
            $(selector).hover(
                function(){
                    $(this).addClass(cls);},
                function(){
                    $(this).removeClass(cls);}
            );
        }

        /* Bind hover events */
        toggleParentOnHover('.tag > .confirm', 'tag-confirm');
        toggleParentOnHover('.tag > .deny', 'tag-deny');
        toggleParentOnHover('.tag > .erase', 'tag-deny');
        toggleClassOnHover('#lbTopContainer .star', 'hover');
        toggleClassOnHover('#lbTopContainer .copy', 'hover');

        function ajaxTagVote(tag, set) {
            ajaxPost({
                tag: tag, // tag.id
                set: set // -1 for downvote, 0 for no vote, 1 for upvote
            }, "/api/tag-vote/",
            function(response) { console.log(response) }
            );
        }

        function vote(instance, up) {
            function unset(tag, id, cls) {
                ajaxTagVote(id, 0);
                delete votes[tag_id];
                tag.removeClass(cls);
            }
            var tag = instance.parent();
            var tag_id = tag.attr('data-tag');
            var cls_confirmed = "tag-confirmed";
            var cls_denied = "tag-denied";
            var is_confirmed = votes[tag_id];
            if (is_confirmed === undefined) { // currently neither confirmed nor denied
                if (up) {
                    ajaxTagVote(tag_id, 1);
                    tag.addClass(cls_confirmed);
                } else {
                    ajaxTagVote(tag_id, -1);
                    tag.addClass(cls_denied);
                }
                votes[tag_id] = up;
            } 
            else if (is_confirmed) { // currently confirmed
                if (up) {
                    unset(tag, tag_id, cls_confirmed);
                } else {
                    ajaxTagVote(tag_id, -1);
                    tag.removeClass(cls_confirmed);
                    tag.addClass(cls_denied);
                    votes[tag_id] = up;
                }
            }
            else { // currently denied
                if (up) {
                    ajaxTagVote(tag_id, 1);
                    tag.removeClass(cls_denied);
                    tag.addClass(cls_confirmed);
                    votes[tag_id] = up;
                } else {
                    unset(tag, tag_id, cls_denied);
                }
            }
        }

        function tagAdd(elem, is_new) {
            var is_new = typeof is_new !== 'undefined' ? is_new : false;
            elem.keydown(function(event) {
                if (event.which == 9) { // tab
                    createTag();
                }
            });

            elem.keypress(function(event) {
                if (event.which == 13 || event.which == 44) { // enter and comma, respectively
                    createTag();
                }
            });

            function createTag() {
                event.preventDefault();
                var content = elem.val();
                if (!validateTag(content) || content.length > context.TAG_MAX_LEN) {
                    elem.select();
                    return;
                }
                elem.val('');
                var new_tag = $('<span/>', {
                    text: content,
                    class: 'user-added tag'
                });
                $('<img/>', {
                    class: 'btn erase'
                }).appendTo(new_tag);
                if (is_new) {
                    new_tag.insertBefore($('#lbCaption input'));
                    new_tag.find('.erase').click(function(){ tagErase($(this), true); });
                } else {
                    var gif_id = elem.attr('data-gif');
                    new_tag.insertBefore($("input[data-gif='" + gif_id + "']"));
                    ajaxTagAdd(gif_id, content);
                }
                toggleParentOnHover('.tag > .erase', 'tag-deny');
            }

            function validateTag(input) {
                return /^[a-zA-Z0-9\. '-]+$/.test(input);
            }
        }

        var tag_add = $('#lbCaption .tag-add');
        var tag_add_new = $('#lbCaption .tag-add-new');
        tag_add.focus();
        tag_add_new.focus();
        tagAdd(tag_add);
        tagAdd(tag_add_new, true);

        function ajaxTagAdd(gif_id, tag) {
            ajaxPost({gif: gif_id,
                      tag: tag
                     }, "/api/tag-add/",
                     function(response) {
                         console.log(response);
                         var result = response.result;
                         var tag_id = response.taginstance;
                         if (result === 0) {
                             $("[data-gif='" + gif_id + "']").each(function() {
                                 var tag = $(this).parent().find('.tag').last();
                                 tag.attr('data-tag', tag_id);
                                 tag.find('.erase').click(function(){ tagErase($(this)); });
                             });
                         } 
                         else {
                             console.error("ResponseError: Error with response recieved from server.");
                             console.log(response);
                         }
                     }
            );
        }

        function tagErase(elem, is_new) {
            var is_new = typeof is_new !== 'undefined' ? is_new : false;
            var tag_id = elem.parent().attr('data-tag');
            if (is_new) {
                elem.parent().remove();
            } else {
                ajaxTagErase(tag_id);
                $("[data-tag='" + tag_id + "']").remove();
            }
        }

        function ajaxTagErase(tag_id) {
            ajaxPost({tag: tag_id},
                     "/api/tag-erase/",
                     function(response) { console.log(response) }
                    );
        }

        function ajaxGetStar(elem) {
            gif_id = elem.attr('data-gif');
            ajaxPost({gif: gif_id},
                     "/api/star-get/",
                     ajaxInterpretStar
                    );
        }

        function ajaxAddStar(elem) {
            gif_id = elem.attr('data-gif');
            ajaxPost({gif: gif_id},
                     "/api/star-add/",
                     function(response) { console.log(response) }
                    );
        }

        function ajaxRemoveStar(elem) {
            gif_id = elem.attr('data-gif');
            ajaxPost({gif: gif_id},
                     "/api/star-remove/",
                     function(response) { console.log(response) }
                    );
        }

        function toggleStar(elem) {
            if (elem.hasClass('selected')) {
                ajaxRemoveStar(elem);
                elem.removeClass('selected');
            } else {
                ajaxAddStar(elem);
                elem.addClass('selected');
            }
        }

        function toggleCopyText(elem) {
            var copy_text = elem.parent().find('.copy-text');
            if (elem.hasClass('selected')) {
                elem.removeClass('selected');
                copy_text.hide();
            } else {
                elem.addClass('selected');
                copy_text.show();
                copy_text.select();
            }
        }

        /* Bind click events */
        $('.tag > .confirm').click(function(){ vote($(this), true); });
        $('.tag > .deny').click(function(){ vote($(this), false); });
        $('.tag > .erase').click(function(){ tagErase($(this)); });
        $('#lbTopContainer .star').click(function(){ toggleStar($(this)); });
        $('#lbTopContainer .copy').click(function(){ toggleCopyText($(this)); });
	}

	function stop() {
		preload.onload = null;
		preload.src = preloadPrev.src = preloadNext.src = activeURL;
		$([center, image, bottom]).stop(true);
		$([prevLink, nextLink, image, aside, topContainer, bottomContainer]).hide();
	}

	function close() {
        if (options.is_new) {
            if (window.confirm("Your GIF has not been added. Are you sure you want to leave?")) { } 
            else { return }
        }
		if (activeImage >= 0) {
			stop();
			activeImage = prevImage = nextImage = -1;
			$(center).hide();
			$(overlay).stop().fadeOut(options.overlayFadeDuration, setup);
		}

		return false;
	}

})(jQuery);

// AUTOLOAD CODE BLOCK (MAY BE CHANGED OR REMOVED)
if (!/android|iphone|ipod|series60|symbian|windows ce|blackberry/i.test(navigator.userAgent)) {
	jQuery(function($) {
		$("a[rel^='lightbox']").slimbox({/* Put custom options here */}, null, function(el) {
			return (this == el) || ((this.rel.length > 8) && (this.rel == el.rel));
		});
	});
}
