var processing = false;
var amountScrolled = 500;
var page = 1;
var category = "";
var myurl = "";
var loader;
var votes = true;
var sockets = {};

$(window).load(function(){
	if ( loader == undefined) {
		loader = $("#load_circle");
	}

	TopButtonScroll();
	ToTop();
	Scroll();

	ClickAjaxMenu();
  BackForwardButtons();
	GifPlay();
	ratePost();
  ReplyBtn();
	AddCommentBtn();
	setTimeout( stubImgs(), 0 );
	hideBanner();
	setTimeout( wsConnect(), 0 );
});

function hideBanner() {
  froalaBanner = $('a[href="https://froala.com/wysiwyg-editor"');
  froalaBanner.hide();
  $('body').bind("DOMSubtreeModified",function(){
      $('a[href="https://froala.com/wysiwyg-editor"').hide();
  });
}


function stubImgs() {
imgs = $('img[src_real');
imgs.each(function() {
	srcset = $(this).attr('srcset_real');
	src = $(this).attr('src');
	$(this).css('min-height', $(this).height()+'px');
	$(this).attr('srcset', srcset);
	$(this).removeAttr('srcset_real');
	$(this).attr('src', src);
	$(this).removeAttr('src_real');
	$(this).css('min-height', '');
});
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
		 stubImgs();
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

function ratePost() {
	$(document).on('click', '.rate-icon', function() {
		if (votes == false) {
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
	//event.preventDefault();
	ajax_menu = $(this);
	if ( ajax_menu.attr("url") != undefined &&
				ajax_menu.attr("url") != ""  )
			{
				//debugger;
			myurl = ajax_menu.attr('url');
			category = "/" + myurl;
			if ( ajax_menu.is("[cat]") ) {
				category = "/cat/" + myurl.toLowerCase();
			}
	}
	else {
		category = "/";
		myurl = ""
	}

		if ( ajax_menu.is('[single_page]' ) ) { // if it is menu don't load on scroll
			single = true;
		}
		else { // if it is list page load on scroll
			single = false;
		}

	$('html, body').scrollTop( 0 );

	if ( ajax_menu.text().replace(/\s/g, '') != "" ) {
		document.title = ajax_menu.text();}
	else {
		document.title = "My blog!";}

	try {
		sockets[window.location.pathname].close();
		console.log("socket "+ sockets[window.location.pathname].url + " CLOSED");
		delete sockets[window.location.pathname];
	}
	catch(err) {}

	//ChangePage();
	window.history.pushState({state:'new'}, "",  category);
	ChangePageNew( category, myurl, single );
	return false;
});
}

function cloneComment( data ) {
	var comment = data;
	var com = $(".sample_comment").clone();
			com.removeClass('sample_comment');
			com.attr('comment_id', comment['id']);
			com.attr('level', comment['level']);
			console.log('level: ' + comment['level'] +
			' com level '+ com.attr('level') );
			com.attr('parent', comment['parent']);
			console.log('parent: ' + comment['parent'] +
			' com parent '+ com.attr('parent') );
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
		console.log("root com");
		$(".comments").append( com );
		com.wrap('<ul><li></li></ul>');
		com.css('display', 'block');
	}

	if (last_child.length > 0) {
		//console.log("append after last child");
		last_child = $( last_child ).parent('li');
		$( last_child ).after(com);
		com.wrap('<li></li>');
	} else {
		//console.log("append after parent");
		if ( parent.length > 0 ) {
			$( parent ).after(com);
			com.wrap('<ul><li></li></ul>');
		}
	}
	com.css('display', 'block');
	stubImgs();
}

function wsConnect() {
if ( $("#Comments_title").length > 0 ) {

	var socket = new ReconnectingWebSocket("ws://" + window.location.host + window.location.pathname);
	socket.onmessage = function(e) {
		sockets[window.location.pathname] = socket;
		try {
			console.log(e.data);
			var elem = JSON.parse(e.data);
			if ( elem['comment'] ) {
				cloneComment(elem);
			}
		} catch(err) {};

	}
	socket.onopen = function() {
		socket.send("hello world");
		console.log("socket "+ socket.url + " opened");
	}
	socket.onclose = function() {
		socket.send("disconnect");
		console.log("socket "+ socket.url + " reconnected");
	}
	// Call onopen directly if socket is already open
	if (socket.readyState == WebSocket.OPEN) socket.onopen();
	}
}

function ChangePageNew( link, myurl, single ) {
	content = $(".content")
	content.fadeTo(0, 0.1);
	loader.css('top', '120px').css('left', '50%').css('position', 'absolute').show();
	$.ajax({
      type:"GET",
		  //cache : false,
		  url: link,
      success:function(data){
      data2 = ('<div class="posts">' + data + '</div>');
      $(data2).replaceAll('.posts');
			content.fadeTo(0, 1);
			$('#load_circle').hide();
			disableRate();
			setTimeout( stubImgs(), 0 );
			wsConnect();
          }
     });
	//window.history.pushState({state:'new'}, "",  link);
   page = 1;

	 $('.menu').parent().removeClass('active');
 	if ( myurl != "" && single == false) {
        $('.menu').filter( $('#'+myurl ) ).parent().addClass('active');
    }

};

function BackForwardButtons() {
	window.onpopstate = function(event) {
		category = document.location.pathname;
		myurl = category.split('/').pop()
	  ChangePageNew(document.location, myurl);
	};

}

function loadMore(){
     $.ajax({
      type:"GET",
		  //cache : false,
      url:category+"?page="+page,
      success:function(data){
               $('.posts').append(data); //adds data to the end of the table
               processing = false; // the processing variable prevents multiple ajax calls when scrolling
							 loader.hide();
							 disableRate();
							 setTimeout( stubImgs(), 0 );
              	//ImageHeight();
          }
     });

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
