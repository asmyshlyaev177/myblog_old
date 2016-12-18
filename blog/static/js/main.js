var processing = false;
var amountScrolled = 500;
var page = 1;
var category = "";
var myurl = "";
var loader;
var votes = true;


$(document).ready(function(){
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
});

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
        }
     });
	 });
}

function AddCommentBtn() {
$(document).on('click', '.btn.add-comment', function (e) {
	form = $("#comment-form");
    btn = $(this);

	if ( $(form).parent().hasClass("comment") ) {
		parent = parseInt($(form).attr("comment_id"));
	} else {
		parent = 0;
	}

	post_id = parseInt( $(form).attr("postid") );
	link = "/add-comment/"+post_id+"/"+parent+"/";
	csrf = getCookie('csrftoken');

	$.ajax({
		  headers: {'X-CSRFToken': csrf},
		  type:"POST",
		  cache : false,
		  data: $(form).serialize(),
		  url: link,
      success:function(data){
		console.log("success!");
		  $(".fr-view").html("")
        }
     });
	return false;
})
}

function ReplyBtn() {
$(document).on('click', '.reply-btn', function() {
	btn = $(this);
	comment = $(btn).parents("div.comment");

	$("#comment-form").attr("comment_id", $(comment).attr("comment_id")) ;
  $(".fr-view").html("");
	$("#comment-form").appendTo(comment);
	return false;
	});
}

function ratePost() {
	$(document).on('click', '.rate-icon', function() {
		if (votes == false) {
			return false;
		}

	vote_btn = this;
	id = $(vote_btn).parent().attr('post');
	rate = $(vote_btn).attr('rate');
	csrf = getCookie('csrftoken');
	$.ajax({
		  headers: {'X-CSRFToken': csrf},
	      type:"POST",
		  //cache : false,
	      url:"/rate/postid-"+id+"-rate-"+rate,
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
			processing = true;
			single = true;
		}
		else { // if it is list page load on scroll
			processing = false;
			single = false;
		}

	$('html, body').scrollTop( 0 );

	if ( ajax_menu.text().replace(/\s/g, '') != "" ) {
		document.title = ajax_menu.text();}
	else {
		document.title = "My blog!";}

	//ChangePage();
	window.history.pushState({state:'new'}, "",  category);
	ChangePageNew( category, myurl, single );
	return false;
});
}


function ChangePageNew( link, myurl, single ) {
	content = $(".content")
	content.fadeTo(0, 0.3);
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
