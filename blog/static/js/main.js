var processing = false;
var amountScrolled = 500;
var page = 1;
var category = "";
var myurl = "";
var loader;
var votes = true;
var sockets = {};
var isTouch =  !!("ontouchstart" in window) || window.navigator.msMaxTouchPoints > 0;
var userAuth = false;

$(window).load(function(){
	if ( loader == undefined) {
		loader = $("#load_circle");
	}

	TopButtonScroll();
	ToTop();
	Scroll();

	ClickAjaxMenu();
  BackForwardButtons();
	//GifPlay();
	rate();
  ReplyBtn();
	AddCommentBtn();
	//setTimeout( stubImgs(), 0 );
	hideBanner();
	setTimeout( wsConnect(), 0 );
	playPause();
	userMenu();
	rateHoverClick();
	checkUserAuth();
});

function userMenu() {
$('.button-collapse').sideNav({
      menuWidth: 300, // Default is 300
      edge: 'right', // Choose the horizontal origin
      closeOnClick: true, // Closes side-nav on <a> clicks, useful for Angular/Meteor
      draggable: true // Choose whether you can drag to open on touch screens
    }
  );
}

function hideBanner() {
  froalaBanner = $('a[href="https://froala.com/wysiwyg-editor"');
  froalaBanner.hide();
  $('body').bind("DOMSubtreeModified",function(){
      $('a[href="https://froala.com/wysiwyg-editor"').hide();
  });
}

function stubImgs() {
	img_new = [];
	imgs = $('img[src_real]');
	for ( var i = 0; i < imgs.length; i++ ) {
		srcset = $(imgs[i]).attr('srcset_real');
		src = $(imgs[i]).attr('src');
		//$(imgs[i]).css('min-height', $(imgs[i]).height()+'px');

		$(imgs[i]).css('opacity', 0.5);
		img_new[i] = new Image();
		img_new[i].onload = function() {
			current_img = $(imgs[ img_new.indexOf(this) ])
			$(current_img).attr('srcset', this.srcset)
				.removeAttr('srcset_real')
				.attr('src', this.src)
			 	.removeAttr('src_real').css('opacity', 1);
			 	//.next('.loader').remove();
			//$(current_img).css('min-height', '');
		}
		img_new[i].srcset = srcset;
		img_new[i].src = src;
		}
	}

function Comments() {
	$(document).ready(function(){
	postid = parseInt( $(".post_header").attr("postid") );
	link = "/comments/" + postid + "/"
	$.ajax({
		  type: "GET",
		  cache : false,
		  url: link,
      success:function(data){
		 $(data).appendTo( $("#Comments_title") );
		 //stubImgs();
        }
     });
	 });
}

function AddCommentBtn() {
	$(document).on('click', '.btn.add-comment', function (e) {
	var form = $("#comment-form");
  var btn = $(this);

	if ( $(form).prev().hasClass("comment") ) {
		var parent = parseInt($(form).attr("comment_id"));
	} else {
		var parent = 0;
	}

	var post_id = parseInt( $(form).attr("postid") );
	var link = "/add-comment/"+post_id+"/"+parent+"/";
	var csrf = getCookie('csrftoken');

	$("#def_form_place").after(form);
	$.ajax({
		  headers: {'X-CSRFToken': csrf},
		  type:"POST",
		  cache : false,
		  data: $(form).serialize(),
		  url: link,
      success:function(data){
			form.hide();
        }
     });
		$(".fr-view").html("");
	return false;
	});
	}

function ReplyBtn() {
	$(document).on('click', '.reply-btn', function() {
		if ( !$("#user_auth").length ) {
			LoginModal();
			return false;
		 }
	var btn = $(this);
	var comment = $(btn).parents("div.comment");
  $("#comment-form-sample").attr("id", "comment-form");
	form = $("#comment-form").detach();
	form.attr("comment_id", $(comment).attr("comment_id")) ;
  $(".fr-view").html("");
	//form.appendTo(comment);
	if ( comment.length > 0 ) {
		  $(comment).after(form);
	 } else {
		 $(this).after(form);
	 }

	form.show();
	return false;
	});
}

function LoginModal() {
	$('<a href="' + '/login?next=' + window.location.pathname + '"></a>').modal();
}

function rateHoverClick() {
	$(document).on('mouseover', '.rate-icon.rate-up', function() {
    $(this).addClass('link-green');
  });
   $(document).on('click', '.rate-icon.rate-up', function() {
    $(this).animate({
			opacity: 0.3},
			100).delay(100)
				.animate({opacity: 1}, 100);
				if ( isTouch ) {
					$(this).removeClass('link-green');
				}
	});
	$(document).on('mouseleave', '.rate-icon.rate-up', function() {
		$(this).removeClass('link-green');
	});

	$(document).on('mouseover', '.rate-icon.rate-down', function() {
    $(this).addClass('link-red');
  });
   $(document).on('click', '.rate-icon.rate-down', function() {
    $(this).animate({
			opacity: 0.3},
			100).delay(100)
				.animate({opacity: 1}, 100);
				if ( isTouch ) {
					$(this).removeClass('link-red');
				}
	});
	$(document).on('mouseleave', '.rate-icon.rate-down', function() {
		$(this).removeClass('link-red');
	});
}

function rate() {
	$(document).on('click', '.rate-icon', function() {
		if (votes == false) {
			return false;
		}

	if ( !$("#user_auth").length ) {
		LoginModal();
		return false;
	 }

	vote_btn = this;
	var el_type = "";
	if ( $(vote_btn).parent().is("[comment]") ) {
		el_type = "comment";
		id = $(vote_btn).parent().attr('comment');
	} else {
		el_type = "post";
		id = $(vote_btn).parent().attr('post');
	}

	rate = $(vote_btn).attr('rate');
	r_url = "/rate/" + el_type +"/"+id+"-rate-"+rate;
	csrf = getCookie('csrftoken');
	$.ajax({
		  headers: {'X-CSRFToken': csrf},
	      type:"POST",
		  //cache : false,
	      url: r_url,
				success:function(data){
					if (data == "no votes") {
						votes = false;
						disableRate();
						console.log(data);
					}
					else {
						//$(vote_btn).animate({opacity: "toggle"}, 300)
						//.animate({opacity: "toggle"}, 200);
					}
				}
	     });
	return false;
	})
}

function disableRate() {
	if (votes == false) {
		$('.rate-icon').css('color', 'gray').css('cursor', 'default');
	}
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// есть webm так что не нужно
function GifPlay() {
	$(document).on('click', '.gif', function() {
		img = $(this).parent().children("img");
		span = $(this).children(".play");
		src = img.attr('src');
		dataalt = img.attr('dataalt');
		img.attr('src', dataalt);
		img.attr('dataalt', src);
		span.toggle();
		return false;
	});
}

function Scroll() {
 $(document).scroll( function() {
  if (processing){
	  return false;
  }
  if ( $(document).scrollTop() > ( ($(document).height() - $(window).height())-300  )) {
	  processing = true; //prevent multiple scrolls once first is hit
	  if ( $( "#last_page" ).length == 0 ) {
			loader.css('top', '').css('left', '').css('position', 'static').show();
			page += 1;
			loadMore();
		}
   }
	});
	}

function loadMore(){
	console.log("load url " + myurl+ "?page=" +page);
     $.ajax({
      type:"GET",
		  //cache : false,
      url:myurl+"?page="+page,
      success:function(data){
							 if ( data != 'last_page') {
								 $('.content').append(data); //adds data to the end of the table
								 //console.log(data);
	               processing = false; // the processing variable prevents
								  									 //multiple ajax calls when scrolling
							 } else {
								 $('.content').append('<p id="last_page"></p>')
							 }

							 loader.hide();
							 disableRate();
          }
     });

}

function ToTop() {
	$(document).on('click', '.back-to-top', function() {
		/*$('html, body').animate({
			scrollTop: 0
		}, 900); */
		$(document).scrollTop(0);
		return false;
	});
	}

function TopButtonScroll(){
	$(document).scroll(function() {
		if ( $(document).scrollTop() > amountScrolled ) {
			$('a.back-to-top').fadeIn('slow');
		} else {
			$('a.back-to-top').fadeOut('slow');
		}
	});
}

function ClickAjaxMenu() {
	$(document).on('click', '.ajax-menu', function() {
	$(".menu").removeClass('active');
	$(this).addClass('active');
	pop = "";
	ajax_menu = $(this);
	if ( ajax_menu.is('[single_page]' ) ) { // if it is menu don't load on scroll
		single = true;
	} else { // if it is list page load on scroll
		single = false;
	}
	if ( ajax_menu.is('[one_col]' ) ) {
		one_col = true;
	} else {
		one_col = false;
	}
	category = ajax_menu.attr('url');

	if ( ajax_menu.attr("url") != undefined &&
				ajax_menu.attr("url") != ""  )
			{
				//debugger;
			if ( ajax_menu.is("[cat]") ) {
				myurl = "/cat/" + category.toLowerCase();
			} else if ( ajax_menu.is("[pop]") ) {
				pop = category.toLowerCase();
			} else {
				myurl = '/' + category.toLowerCase();
			}
	}
	else {
		myurl = "/";
		category = ""
	}

	$('html, body').scrollTop( 0 );

	if ( ajax_menu.text().replace(/\s/g, '') != "" ) {
		document.title = ajax_menu.text();}
	else {
		document.title = "My blog!";}

	//Change Page
	if ( pop ) {
		if ( myurl == "/" ) {
			url = myurl + pop;
		} else {
			url = myurl + '/' + pop;
		}
	} else {
		url = myurl;
	}

		window.history.pushState({state:'new'}, "",  url);
		ChangePageNew( url, category, single, one_col);
		return false;

	});
	}

function ChangePageNew( link, category, single_page, one_col ) {
		content = $(".content")
		content.fadeTo(0, 0.1);
		//try {
			for ( socket in sockets ) {
				sockets[socket].close();
				//delete sockets[socket];
			}
		//} catch(err) {}

		loader.css('top', '120px').css('left', '50%').css('position', 'absolute').show();
		$.ajax({
	      type:"GET",
			  //cache : false,
			  url: link,
	      success:function(data){
					content.fadeTo(0, 1);
					$('#load_circle').hide();
					disableRate();
					$("#login-link").attr("href", "/login?next=" + window.location.pathname);
					$("#logout-link").attr("href", "/logout?next=" + window.location.pathname);
					if ( one_col ) {
						$(".main").attr('class', 'main col s12 m12 l12');
						$(".sidebar").hide();
					} else {
						$(".main").attr('class', 'main col s12 m10 l6 offset-m1 offset-l1');
						$(".sidebar").show();
					}
					data2 = ('<div class="content">' + data + '</div>');
					$(data2).replaceAll('.content');
					if ( $("div.post").length < 2 && single_page) {
					 $(".pop-tabs").hide();
				 } else {
					 $(".pop-tabs").show();
					 $(".categories").show();
				 };

	          }
	     });

	   page = 1;
		$(".menu").parent().removeClass('active');

	 	if ( category != "" && single_page == false) {
					link = link.split('/');
					pop = link.pop();
					cat = link.pop();
					if ( pop == "pop-all" || pop == "pop-best") {
									$('.menu').filter( $('#'+pop ) ).parent().addClass('active');
									$('.menu').filter( $('#'+cat ) ).parent().addClass('active');
								} else {
									$('.menu').filter( $('#'+category ) ).parent().addClass('active');
								}
	    }

		};

function cloneComment( data ) {
	var comment = data;
	var com = $(".sample_comment").clone();
			com.removeClass('sample_comment');
			com.attr('comment_id', comment['id']);
			com.attr('level', comment['level']);
			com.attr('parent', comment['parent']);
			com.css('margin-left', comment['level']*25+'px');
			com.find('.comment_text').html(comment['text']);
			com.find('.comment_user_avatar').children().attr('src', '/static' + comment['avatar']);
			com.find('.comment_username').html( comment['author'] );
			com.find('.comment-date').html( comment['created'] );

	if ( parseInt(comment['level']) > 0 ) {
		var p_str = "[comment_id="+parseInt(comment['parent']) +"]" ;
		var parent = $( p_str );
		var last_child = $("[parent="+parseInt(comment['parent']) +"]").last();
	} else {
		$(".comments").append( com );
		com.wrap('<ul><li></li></ul>');
		com.css('display', 'block');
	}

	if (last_child.length > 0) {
		last_child = $( last_child ).parent('li');
		$( last_child ).after(com);
		com.wrap('<li></li>');
	} else {
		if ( parent.length > 0 ) {
			$( parent ).after(com);
			com.wrap('<ul><li></li></ul>');
		}
	}
	com.css('display', 'block');
	//stubImgs();
}

function checkUserAuth() {
	if ( $("#user_auth").length > 0 ) {
		userAuth = true;
	} else {
		userAuth = false }
}

function wsConnect() {
	if ( $(".socket").length > 0 && userAuth ) {

		var socket = new ReconnectingWebSocket(
			"ws://" + window.location.host + '/ws/' +
			decodeURIComponent(window.location.pathname).split('/').filter(Boolean).slice(-1)[0], null,
			{maxReconnectInterval: 2000, maxReconnectAttempts: 10});
		socket.onmessage = function(e) {
			try {
				var elem = JSON.parse(e.data);
				if ( elem['comment'] ) {
					cloneComment(elem);
				}
			} catch(err) {};

		}
		socket.onopen = function() {
			//socket.send("hello world");
			sockets[window.location.pathname] = socket;
		}
		//socket.onclose = function() {
			//socket.send("disconnect");
		//}
		// Call onopen directly if socket is already open
		if (socket.readyState == WebSocket.OPEN) socket.onopen();
		}
	}

function BackForwardButtons() {
	window.onpopstate = function(event) {
		url = document.location.pathname;
	  ChangePageNew(url);
	};

}

function HintPos() {
	var offset = $(".tt-input").offset();
	var topOffset = $(".tt-input").offset().top- $(window).scrollTop();

	  /* position of hints */
		 $(".tt-menu").css({
	        position: "fixed",
	        top: (topOffset + 35)+ "px",
	        left: (offset.left) + "px",
	    });
}

function CopyTags() {
	$(".hidden_tags").val($("#tagBox").tagging( "getTags" ).toString());
}

function SelectHint() {
	$(document).on({
	    mouseenter: function () {
			$(".tt-suggestion").removeClass("tt-cursor");
	        $(this).addClass("tt-cursor");
	    },
	    mouseleave: function () {
	        $(this).removeClass("tt-cursor");
	    }
	}, ".tt-suggestion");
	}

function HideHint() {
  $('.tt-menu').hide();
}

function Preview( files, el_id, height ) {
	preview = document.getElementById(el_id)
	preview.src = window.URL.createObjectURL(files);
	preview.height = height;
  }


//
function playPause() {
	$(document).on('click', 'video', function(e) {
		if ( this.paused ) {
			this.play();
		} else {
			this.pause();
		}
	});
 }
