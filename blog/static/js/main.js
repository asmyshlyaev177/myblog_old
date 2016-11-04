var processing = false;
var amountScrolled = 100;
var page = 1;
var category = "";
var myurl = "";
var loader;


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
});

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
		}
		else { // if it is list page load on scroll
			processing = false;
		}

	$('html, body').scrollTop( 0 );

	if ( ajax_menu.text().replace(/\s/g, '') != "" ) {
		document.title = ajax_menu.text();}
	else {
		document.title = "My blog!";}

	//ChangePage();
	window.history.pushState({state:'new'}, "",  category);
	ChangePageNew( category, myurl );
	return false;
});
}


function ChangePageNew( link, myurl ) {
	content = $(".content")
	content.fadeTo(70, 0.3);
	loader.css('top', '120px').css('left', '50%').css('position', 'absolute').show();
	$.ajax({
      type:"GET",
		  //cache : false,
		  url: link,
      success:function(data){
      data2 = ('<div class="posts">' + data + '</div>');
      $(data2).replaceAll('.posts');
			content.fadeTo(130, 1);
			$('#load_circle').hide();
          }
     });
	//window.history.pushState({state:'new'}, "",  link);
   page = 1

	 $('.menu').parent().removeClass('active');
 	if ( myurl != "" ) {
 	$('.menu').filter( $('#'+myurl ) ).parent().addClass('active');}

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
