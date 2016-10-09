var processing = false;
var amountScrolled = 100;
page = 1;
category = ""

$(document).ready(function(){
	BackToTop()
	
});

$('a.back-to-top').click(function() {
	$('html, body').animate({
		scrollTop: 0
	}, 900);
	return false;
});

$('.ajax-menu').click( function() {
	event.preventDefault();
	category = $( this ).attr('url')
		if ( $(this).is('[single_page]' ) ) { // if it is menu don't load on scroll
			processing = true;
		}
		else { // if it is list page load on scroll
			processing = false;
		}
	$('.ajax-menu').parent().removeClass('active')
	if ( $(this).parent().is('[role]') ){
		$(this).parent().addClass('active')
	}
	
	ChangePage();
});

function ChangePage() {
	$.ajax({
          type:"GET",
		  cache : false,
          url:category,  
          success:function(data){
             data2 = ('<div class="content">' + data + '</div>');
               $(data2).replaceAll('.content');
          }
     });
	 // change browser url string ;)
	 window.history.pushState("object or string", category, category );
page = 1
}

function loadMore(){
     $.ajax({
          type:"GET",
		  cache : false,
          url:"?page="+page,
          success:function(data){
               $('.content').append(data); //adds data to the end of the table
               $('#more-loader').toggle()
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
                $('#more-loader').toggle()
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

