/*
	Taglight - a custom implementation of:
    Slimbox v2.05 - The ultimate lightweight Lightbox clone for jQuery
	(c) 2007-2013 Christophe Beyls <http://www.digitalia.be>
	MIT-style license.
*/

CAPTION_WIDTH = 220;
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
            is_unsaved: false,            // Is the gif being created, or are we just viewing it? (user-added)
			loop: false,				// Allows to navigate between first and last images
			overlayOpacity: 0.8,			// 1 is opaque, 0 is completely transparent (change the color in the CSS file)
			overlayFadeDuration: 0,		// Duration of the overlay fade-in and fade-out animations (in milliseconds)
			resizeDuration: 1,			// Duration of each of the box resize animations (in milliseconds)
			resizeEasing: "swing",			// "swing" is jQuery's default easing
			initialWidth: 48,			// Initial width of the box (in pixels)
			initialHeight: 48,			// Initial height of the box (in pixels)
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

            var spinner_top = parseInt($(center).css('height'))/2 - options.initialHeight/2;
            $(center).css({'top': "+="+spinner_top, 'height': options.initialHeight+'px'});
            lb_spinner_id = typeof lb_spinner_id === 'undefined' ? animateSpinner($('.lbLoading'), options.initialWidth, 12) : lb_spinner_id;

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

        var tag_add = $('#lbCaption .tag-add');
        var tag_add_new = $('#lbCaption .tag-add-new');

        function focusTagInput() {
            tag_add.focus();
            tag_add_new.focus();
        }

        tagAdd(tag_add);
        tagAdd(tag_add_new, true);

        /* have we already voted on this tag? color tags accordingly. */
        function colorTags() {
            $('#lbCaption .tag').each(function(){
                colorSpecialTags($(this));
                if (context.user.is_authenticated) {
                    var tag_id = $(this).attr('data-tag');
                    ajaxPost({tag: tag_id}, "/api/tagvote-get/", ajaxInterpretTagVote);
                }
            });
        }

        function colorSpecialTags(tag) {
            if (tag.text().toLowerCase() === "nsfw")
                tag.addClass('nsfw');
        }

        function constrainNumTags(is_new) {
            var num_tags = $('#lbCaption .tag').length;
            var input = $('#lbCaption input');
            if (num_tags > 11) {
                input.prop('disabled', true);
            } else if (num_tags < 5) {
                if (!is_new)
                    allowTagErase(false, is_new);
                input.prop('disabled', false);
            } else {
                allowTagErase(true, is_new);
                input.prop('disabled', false);
            }
        }

        function allowTagErase(allowed, is_new) {
            var erase_buttons = $('#lbCaption .tag > .erase');
            if (allowed) {
                erase_buttons.removeClass('disabled-tmp');
                erase_buttons.not('.bound, .disabled').click(function(){ tagErase($(this), is_new); }).addClass('bound');
            } else {
                erase_buttons.unbind('click').removeClass('bound').addClass('disabled-tmp');
            }
        }

        function ajaxInterpretTagVote(response) {
            var tag = response.tag;
            var v = response.vote;
            elem = $('.tag[data-tag='+tag+']');
            if (v !== 0) {
                if (v === 1) {
                    votes[tag] = true;
                    elem.addClass("confirmed");
                }
                else if (v === -1) {
                    votes[tag] = false;
                    elem.addClass("denied");
                }
                else
                    console.error("GetTagVoteError: server did not return a valid TagVote");
            }
        }

        colorTags();

        function ajaxInterpretStar(response) {
            if (response.star === 1)
                $('#lbTopContainer .star').addClass('selected').prop('title', "Remove from starred");
        }

        ajaxGetStar();

		if (prevImage >= 0) $(prevLink).show();
		if (nextImage >= 0) $(nextLink).show();
		$(bottom).css("marginTop", -bottom.offsetHeight).animate({marginTop: 0}, options.captionAnimationDuration);
		aside.style.visibility = topContainer.style.visibility = bottomContainer.style.visibility = "";
       
        function toggleParentOnHover(elem, cls) {
            elem.hover(
                function(){
                    $(this).parent().addClass(cls); },
                function(){
                    $(this).parent().removeClass(cls); }
            );
        }

        function toggleClassOnHover(elem, cls) {
            elem.hover(
                function(){
                    $(this).addClass(cls); },
                function(){
                    $(this).removeClass(cls); }
            );
        }

        /* Bind hover events */
        toggleParentOnHover($('#lbCaption .tag > .confirm'), 'confirm');
        toggleParentOnHover($('#lbCaption .tag > .deny'), 'deny');
        toggleParentOnHover($('#lbCaption .tag > .erase').not('.disabled, .disabled-tmp'), 'deny');
        toggleClassOnHover($('#lbTopContainer .star'), 'hover');
        toggleClassOnHover($('#lbTopContainer .copy'), 'hover');
        $('#lbTopContainer .dropdown, #lbTopContainer .menu').hover(
            function() {
                if (typeof lb_menu_timeout !== 'undefined') clearTimeout(lb_menu_timeout);
                $('#lbTopContainer .btn.dropdown').addClass('hover');
                $('#lbTopContainer .menu').show(); },
            function() { lb_menu_timeout = setTimeout(function () {
                $('#lbTopContainer .btn.dropdown').removeClass('hover');
                $('#lbTopContainer .menu').hide(); }, 150) }
        );

        function ajaxTagVote(tag, set) {
            ajaxPost({
                tag: tag, // tag.id
                set: set // -1 for downvote, 0 for no vote, 1 for upvote
            }, "/api/tag-vote/",
            function(response) { console.log(response) }
            );
        }

        function vote(instance, up) {
            if (loginRequired('tag_vote'))
                return;
            function unset(tag, id, cls) {
                ajaxTagVote(id, 0);
                delete votes[tag_id];
                tag.removeClass(cls);
            }
            var tag = instance.parent();
            var tag_id = tag.attr('data-tag');
            var cls_confirmed = "confirmed";
            var cls_denied = "denied";
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
            focusTagInput();
        }

        function tagAdd(elem, is_new) {
            var is_new = typeof is_new !== 'undefined' ? is_new : false;
            elem.keydown(function(event) {
                if (event.which == 9) { // tab
                    createTag(event);
                }
            });

            elem.keypress(function(event) {
                if (event.which == 13 || event.which == 44) { // enter and comma, respectively
                    createTag(event);
                }
            });

            function createTag(event) {
                if (loginRequired('tag_add'))
                    return;
                event.preventDefault();
                var content = elem.val().toLowerCase();
                if (!validateTag(content) || content.length > context.TAG_MAX_LEN) {
                    elem.select();
                    $('#lbCaption .error').text("Tags may only contain letters, numbers, spaces, and the following characters: period (.), apostrophe ('), hyphen (-).").stop().css("opacity", "1").fadeTo(12000, 0.6);
                    return;
                }
                elem.val('');
                var new_tag = $('<span/>', {
                    text: content,
                    class: 'user-added tag unverified'
                });
                $('<img/>', {
                    class: 'btn erase',
                    src: context.STATIC_URL+'img/tag-erase.png'
                }).appendTo(new_tag);
                colorSpecialTags(new_tag); 
                if (is_new) {
                    new_tag.insertBefore($('#lbCaption input'));
                    new_tag.find('.erase').click(function(){ tagErase($(this), true); });
                    checkValidForSave();
                } else {
                    var gif_id = elem.attr('data-gif');
                    new_tag.insertBefore($("input[data-gif='" + gif_id + "']"));
                    ajaxTagAdd(gif_id, content);
                }
                toggleParentOnHover(new_tag.find('.erase'), 'deny');
            }

            function validateTag(input) {
                return /^[a-z0-9\. '-]+$/.test(input);
            }
        }

        function checkValidForSave() {
            var save_button = $('#lbCaption .save');
            if ($('#lbCaption .tag').length > 3) {
                enableGifSave();
            } else {
                disableGifSave();
            }
        }

        function enableGifSave() {
            var save_button = $('#lbCaption button.save');
            $('#lbCaption .save:not(.bound)').addClass('bound').click(function(){ saveGif(); });
            save_button.removeClass('disabled');
        }

        function disableGifSave() {
            var save_button = $('#lbCaption button.save');
            save_button.removeClass('bound').unbind('click');
            save_button.addClass('disabled');
        }

        function saveGif() {
            disableGifSave();
            var save_button = $('#lbCaption button.save');
            var add_tag = $('#lbCaption .tag-add-new')
            var save_spinner = $('.lbLoading.save');
            var tags = [];
            save_button.text('Saving...');
            animateSpinner(save_spinner, 22, 8);
            save_spinner.show();
            add_tag.slideUp('fast');
            $('#lbCaption .erase').addClass('disabled').unbind('click');
            $('#lbCaption .tag').each(function(){
                tags.push($(this).text());
            });
            console.log("saving gif " + add_gif_filename);
            ajaxPost(
                {filename: add_gif_filename, tags: tags},
                '/api/gif-add/',
                gifSaved
            );
        }

        function gifSaved(response) {
            if (response.result === 0) {
                options.is_unsaved = false;
                var save_button = $('#lbCaption button.save');
                save_button.addClass('success').text('Saved!');
                $('.lbLoading.save').hide();
                $('<button/>', {
                    text: 'Add Another',
                    class: 'medium',
                    id: 'add-another'
                }).click(addGifModal).insertAfter(save_button);
            } else alert(response);
        }

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
                checkValidForSave();
            } else {
                ajaxTagErase(tag_id);
                $("[data-tag='" + tag_id + "']").remove();
            }
            constrainNumTags(is_new);
            focusTagInput();
        }

        function ajaxTagErase(tag_id) {
            ajaxPost({tag: tag_id},
                     "/api/tag-erase/",
                     function(response) { console.log(response) }
            );
        }

        function ajaxGetStar() {
            gif_id = tag_add.attr('data-gif');
            ajaxPost({gif: gif_id},
                     "/api/star-get/",
                     ajaxInterpretStar
            );
        }

        function ajaxAddStar() {
            gif_id = tag_add.attr('data-gif');
            ajaxPost({gif: gif_id},
                     "/api/star-add/",
                     function(response) { console.log(response) }
            );
        }

        function ajaxRemoveStar() {
            gif_id = tag_add.attr('data-gif');
            ajaxPost({gif: gif_id},
                     "/api/star-remove/",
                     function(response) { console.log(response) }
            );
        }

        function toggleStar(elem) {
            if (loginRequired('star'))
                return;
            if (elem.hasClass('selected')) {
                ajaxRemoveStar();
                elem.removeClass('selected');
                elem.prop('title', "Add to starred");
            } else {
                ajaxAddStar();
                elem.addClass('selected');
                elem.prop('title', "Remove from starred");
            }
            focusTagInput();
        }

        function toggleCopyText(elem) {
            elem.tipsy('hide');
            var copy_text = elem.parent().find('.copy-text');
            if (elem.hasClass('selected')) {
                elem.removeClass('selected');
                copy_text.hide();
                focusTagInput();
            } else {
                elem.addClass('selected');
                copy_text.show();
                copy_text.select();
            }
        }

        function ajaxFlagOneStep(gif_id, flag_type) {
            ajaxPost({gif: gif_id, type: flag_type}, '/api/flag-add/', flagConfirmation);
            $('#lbTopContainer .menu').hide();
        }

        function flagConfirmation() {
            $('#action-confirmation').show();
            setTimeout(function(){ $('#action-confirmation').fadeOut(1000) }, 4000);
        }

        function lbModal(modal_id) {
            var modal = $('.modal#'+modal_id);
            var mask = $('.modal-mask');
            var add_gif = $('button.add-gif').addClass('disabled').unbind('click'); // disable the add GIF modal so it doesn't conflict
            var input = modal.find('input');
            modal.show();
            mask.show();
            input.focus();
            mask.click(function(){
                modal.hide();
                $(this).unbind('click');
                mask.hide();
                add_gif.removeClass('disabled').click(addGifModal);
                console.log("rebound addGifModal");
            });
            return modal;
        }

        function ajaxFlagDuplicate(filename) {
            ajaxPost(
                {'gif': tag_add.attr('data-gif'),
                 'type': 'du',
                 'filename': filename},
                "/api/flag-add/",
                flagDuplicateCallback);
        }

        function flagDuplicateCallback(response) {
            $('.lbLoading.check-gif').hide();
            var input = $('.modal input:visible');
            if (response.result) {
                if (response.error === "DoesNotExist")
                    badGif("Whoops, that's not a link to a GIF in GIFdatabase.");
                else
                    alert("Oh no! Something went wrong. Please report this error: \n" + response.error + ": " + response.message);
            } else {
                input.val('');
                $('.modal:visible .error').text('');
                $('.modal, .modal-mask').unbind('click').hide();
                flagConfirmation();
                $('button.add-gif').removeClass('disabled').click(addGifModal);
            }
            input.prop('disabled', false);
        }

        /* Bind click events */
        $('#lbCaption .tag > .confirm').click(function(){ vote($(this), true); });
        $('#lbCaption .tag > .deny').click(function(){ vote($(this), false); });
        $('#lbCaption .tag > .erase').not('.disabled').click(function(){ tagErase($(this)); }).addClass('bound');
        constrainNumTags(false);
        $('#lbTopContainer .star').click(function(){ toggleStar($(this)); });
        $('#lbTopContainer .copy').click(function(){ toggleCopyText($(this)); });
        $('#lbTopContainer #flag-broken').click(function(){ ajaxFlagOneStep(tag_add.attr('data-gif'), 'mi'); });
        $('#lbTopContainer #flag-inappropriate').click(function(){ ajaxFlagOneStep(tag_add.attr('data-gif'), 'in'); });
        $('#lbTopContainer #flag-duplicate').click(function(){
            lbModal('flag-duplicate');
            var flag_duplicate = $('#flag-duplicate input');
            flag_duplicate.on('input', function(){ gifInputChange(flag_duplicate, ajaxFlagDuplicate) });
        });
        $('#lbTopContainer #propose-substitute').click(function(){ lbModal('propose-substitute'); });

        $('#lbTopContainer .star, #lbTopContainer .dropdown').tipsy({gravity: 's'});
        $('#lbTopContainer .copy').tipsy({gravity: 'e'});
        $('#lbCaption .disabled').tipsy({gravity: 's'});

        focusTagInput();
	}

	function stop(interval_id) {
		preload.onload = null;
		preload.src = preloadPrev.src = preloadNext.src = activeURL;
		$([center, image, bottom]).stop(true);
		$([prevLink, nextLink, image, aside, topContainer, bottomContainer]).hide();
	}

	function close() {
        if (options.is_unsaved) {
            if (window.confirm("Your GIF has not been added. Are you sure you want to leave?")) { } 
            else { return }
        }
		if (activeImage >= 0) {
			stop();
			activeImage = prevImage = nextImage = -1;
			$(center).hide();
			$(overlay).stop().fadeOut(options.overlayFadeDuration, setup);
		}

        $('.search input').focus();
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
