var processing = false;
var amountScrolled = 100;
var page = 1;
var category = ""

$(document).ready(function(){
	BackToTop();
	ClickAjaxMenu();
	
	$(document).on('mouseover', "input[value='Add Post']", function(event) {
		ImgResponsive()
	});

	$(document).on('focusout', ".note-editable", function() {
		ImgResponsive();
	});
});

$(document).on('click', 'a.back-to-top', function() {
	$('html, body').animate({
		scrollTop: 0
	}, 900);
	return false;
});



function ImgResponsive() {
	$('img').addClass('img-responsive').css("width", "auto");
}

function ClickAjaxMenu() {
$(document).on('click', '.ajax-menu', function() {
	event.preventDefault();
	menu = $(this);
	url = menu.attr('url');
	category = url;
		if ( menu.is('[single_page]' ) ) { // if it is menu don't load on scroll
			processing = true;
		}
		else { // if it is list page load on scroll
			processing = false;
		}
		
	$('.menu').parent().removeClass('active');
	if ( category != "" && category.search("/") == -1 ) {
	$('.menu').filter( $('#'+category ) ).parent().addClass('active');}

	$('html, body').scrollTop( 0 );
	
	if ( menu.text().replace(/\s/g, '') != "" ) {
		document.title = menu.text();}
	else {
		document.title = "My blog!";}
	ChangePage();
});	
}

function ChangePage() {
	$.ajax({
          type:"GET",
		  //cache : false,
          url:'/'+category,  
          success:function(data){
             data2 = ('<div class="content">' + data + '</div>');
             $(data2).replaceAll('.content');
          }
     });
	 // change browser url string ;)
	 if ( category == "" ) {
		 window.history.pushState("object or string", category, "/" ); }
	 else {
		window.history.pushState("object or string", category, "/"+category ); }
page = 1;
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


function BackToTop(){
	$(document).scroll(function() {
		if ( $(document).scrollTop() > amountScrolled ) {
			$('a.back-to-top').fadeIn('slow');
		} else {
			$('a.back-to-top').fadeOut('slow');
		}
	});
}

