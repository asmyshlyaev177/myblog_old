var processing = false;
var amountScrolled = 100;
var page = 1;
var category = "";
var myurl = "";

$(document).ready(function(){

	TopButtonScroll();
	ToTop();
	Scroll();

	ClickAjaxMenu();
  BackForwardButtons();
	GifPlay();
});

function GifPlay() {
	$(document).on('click', '.gif', function() {
		event.preventDefault();
		img = $(this).parent().children("img");
		span = $(this).children(".play");
		src = img.attr('src');
		dataalt = img.attr('dataalt');
		img.attr('src', dataalt);
		img.attr('dataalt', src);
		span.toggle();
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
		$('#more-loader').toggle();
		page += 1;
		loadMore();
		}
  }
});
}


function ToTop() {
$(document).on('click', 'a.back-to-top', function() {
	$('html, body').animate({
		scrollTop: 0
	}, 900);
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
	event.preventDefault();
	ajax_menu = $(this);
	if ( ajax_menu.attr("url") != undefined &&
				ajax_menu.attr("url") != ""  )
			{
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
});
}


function ChangePageNew( link, myurl ) {
	$.ajax({
      type:"GET",
		  //cache : false,
		  url: link,
      success:function(data){
      data2 = ('<div class="content">' + data + '</div>');
      $(data2).replaceAll('.content');
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
               $('.content').append(data); //adds data to the end of the table
               $('#more-loader').toggle();
               processing = false; // the processing variable prevents multiple ajax calls when scrolling
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
