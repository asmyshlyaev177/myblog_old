"use strict";

var scrollProcessing = false;
var amountScrolled = 500;
var page = 1;
var pageUrl = "";
var catUrl = "";
var catTab = "";
var pop = "";
var loader;
var noVotes = true;
var sockets = {};
var isTouch =  !!("ontouchstart" in window) || window.navigator.msMaxTouchPoints > 0;
var userAuth = false;
var sidebarUrl = "/sidebar/";
var single_page = false;
var main = $(".main");
var sidebar = $(".sidebar");

$(window).load(function(){
	if ( loader == undefined || loader == "" ) {
		loader = $("#loader");
	}
    detectPageUrl();
    toggleCol();
    selectActiveTabs();
    toggleTopMenu();
    checkUserAuth();
    scrollProcessingCheck();
	TopButtonScroll();
	ToTop();
	Scroll();
	ClickAjaxMenu();
    BackForwardButtons();
	rate();
    ReplyBtn();
	AddCommentBtn();
	hideBanner();
	playPause();
	userMenu();
	rateHoverClick();
    wsConnect();
    Comments();
    editorInit();
    tagBoxInit();
});

function scrollProcessingCheck() {
    /* Включаем скроллинг если больше 2 постов*/
    if ( $("div.post").length < 2) {
        scrollProcessing = true;
        } else {
            scrollProcessing = false
        }
}

function userMenu() {
    /* закрываем меню пользователи при клики по пункту */
    $(document).on('click', '#user-menu-list > li > a', function(e) {
       $("#user-menu").dropdown('close');
    });
    $(document).on('click', '#user-menu', function(e) {
        return false;
    });
}

function hideBanner() {
    /* скрываем баннер от Froala */
  var froalaBanner = $('a[href="https://froala.com/wysiwyg-editor"');
  froalaBanner.hide();
  $('body').bind("DOMSubtreeModified",function(){
      $('a[href="https://froala.com/wysiwyg-editor"').hide();
  });
}

function Comments() {
    /* Берём пост ид и загружаем комменты для него */
	$(document).ready(function() {
    if ( $("#Comments_title").length > 0 ) {
        var postid = parseInt( $(".post_header").attr("postid") );
        var link = "/comments/" + postid + "/"
        $.ajax({
            type: "GET",
            cache : false,
            url: link,
            async: false,
            timeout: 5000,
            success: function(data){
            $(data).appendTo( $("#Comments_title") );
            },
        });
    }
	
	 });
}

function AddCommentBtn() {
    /* кнопка отправки коммента */
	$(document).on('click', '.btn.add-comment', function (e) {
        var form = $("#comment-form");
        var btn = $(this);

        if ( $(form).prev().hasClass("comment") ) {
            /* берём ид родительского коммента если он есть */
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
              timeout: 5000,
          success:function(data){
                form.hide();
            }
         });
            /* очищаем поле ввода */
            $(".fr-view").html("");
        return false;
	});
	}

function ReplyBtn() {
    /* кнопка ответа на коммент*/
	$(document).on('click', '.reply-btn', function() {
        /* если юзер не залогинен запрос на авторизацию */
		if ( !$("#user_auth").length ) {
			LoginModal();
			return false;
		 }
	var btn = $(this);
	var comment = $(btn).parents("div.comment");
  /* копируем шаблон коммента */
  $("#comment-form-sample").attr("id", "comment-form");
  var form = $("#comment-form").detach();
  form.attr("comment_id", $(comment).attr("comment_id")) ;
  $(".fr-view").html("");
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
    /* модальное окно авторизации */
	$('<a href="' + '/login?next=' + window.location.pathname + '"></a>').modal();
}

function rateHoverClick() {
    /* добавляем классы для кнопок рейта при наведении курсором */
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
    /* отправка голоса -/+ */
	$(document).on('click', '.rate-icon', function() {
		if ( noVotes == false) {
			return false;
		}

	if ( !$("#user_auth").length ) {
		LoginModal();
		return false;
	 }

	var vote_btn = this;
	var el_type = "";
	if ( $(vote_btn).parent().is("[comment]") ) {
		el_type = "comment";
		var id = $(vote_btn).parent().attr('comment');
	} else {
		el_type = "post";
		var id = $(vote_btn).parent().attr('post');
	}

	var rate = $(vote_btn).attr('rate');
	var r_url = "/rate/" + el_type +"/"+id+"-rate-"+rate;
	var csrf = getCookie('csrftoken');
	$.ajax({
		  headers: {'X-CSRFToken': csrf},
	      type:"POST",
		  //cache : false,
	      url: r_url,
          timeout: 5000,
            success:function(data){
                if (data == "no votes") {
                    noVotes = false;
                    disableRate();
                    console.log(data);
                }
            }
	     });
	return false;
	})
}

function disableRate() {
    /* отключаем кнопки голосования если закончились голоса у пользователя */
	if (noVotes == false) {
		$('.rate-icon').css('color', 'gray').css('cursor', 'default');
	}
}

function getCookie(name) {
    /* получаем куки */
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

function Scroll() {
    /* загрузка страниц при скролле */
 $(document).scroll( function() {
  if (scrollProcessing){
	  return false;
  }
  if ( $(document).scrollTop() > ( ($(document).height() - $(window).height())-400  )) {
	  scrollProcessing = true; // чтобы не срабатывало несколько раз
	  if ( $( "#last_page" ).length == 0 ) {
			loader.css('top', '90%').css('left', '45%').css('position', 'fixed').show();
			page += 1;
			loadMore();
		}
   }
	});
	}

function loadMore(){
    /* функция загрузки страниц для скролла */
	console.log("load url " + pageUrl+ "?page=" +page);
     $.ajax({
      type:"GET",
		  //cache : false,
      url:pageUrl+"?page="+page,
      timeout: 5000,
      success:function(data){
         if ( data != 'last_page') {
             $('.content').append(data); //adds data to the end of the table
             //console.log(data);
               scrollProcessing = false; // the processing variable prevents
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
    /* при клике на кнопке вверх */
	$(document).on('click', '.back-to-top', function() {
		/*$('html, body').animate({
			scrollTop: 0
		}, 900); */
		$(document).scrollTop(0);
		return false;
	});
	}

function TopButtonScroll(){
    /* показывать кнопку если прокрутить ниже amountScrolled */
	$(document).scroll(function() {
		if ( $(document).scrollTop() > amountScrolled ) {
			$('a.back-to-top').fadeIn('slow');
		} else {
			$('a.back-to-top').fadeOut('slow');
		}
	});
}

function ClickAjaxMenu() {
    /* при клике на ссылку которая должна грузиться через ajax */
	$(document).on('click', '.ajax-menu', function() {
	$(".menu").removeClass('active');
	$(this).addClass('active');
	var pop = "";
	var ajax_menu = $(this);
	if ( ajax_menu.is('[single_page]' ) ) { // если страница одна вырубаем скрол
		single_page = true;
	} else { 
		single_page = false;
	}

	if ( ajax_menu.attr("url") != undefined &&
				ajax_menu.attr("url") != "" )
			{ // url для запроса
			if ( ajax_menu.is("[cat]") ) {
                catUrl = ajax_menu.attr('url');
				pageUrl = "/cat/" + catUrl;
				sidebarUrl = "/sidebar/" + catUrl;
			} else if ( ajax_menu.is("[pop]") ) {
                pop = ajax_menu.attr('url');
                if (catUrl == "" ) {
                    pageUrl = "/" + pop;
                } else {
                    pageUrl = "/cat/" + catUrl + '/' + pop;
                }
                    
			} else {
                pageUrl = ajax_menu.attr('url');
            }
	} 
    if ( ajax_menu.is(".brand-logo") ) {
        sidebarUrl = "/sidebar/";
        pageUrl = "/";
		catUrl = ""
    }

	$('html, body').scrollTop( 0 );
    /* если в ссылке текст ставим текст в заголовок окна иначе название сайта */
	if ( ajax_menu.text().replace(/\s/g, '') != "" ) {
		document.title = ajax_menu.text();}
	else {
    document.title = "My blog!";}

    window.history.pushState({state:'new'}, "",  pageUrl); // добавляем новый адрес в историю
    detectPageUrl();
    selectActiveTabs();
    ChangePageNew( pageUrl );
    return false;

	});
	}

function toggleCol() {
    /* Переключает между видом с 1 и 2 колонками */
    if ($("#one-col").length && $(sidebar).css('display') != 'none' ) { 
         oneCol()
    } else if ( $(sidebar).css('display') == 'none' ){
        twoCol()
    }
}

function oneCol() {
    /* форматируем вид в одну колонку */
    $(main).attr('class', 'main col s12 m12 l12');
	$(sidebar).hide();
}

function twoCol() {
    /* в две колонки */
    $(main).attr('class', 'main col s12 m10 l6 offset-m1 offset-l1');
	$(sidebar).show();
}

function ChangePageNew( link ) {
    /* смена страницы через ajax */
        loader.css('top', '39%').css('left', '45%').css('position', 'absolute').show(); // показываем кольцо загрузки
		var content = $(".content");
		content.fadeTo(0, 0.1);
		//try {
			for ( var socket in sockets ) { // удаляем сокет текущей страницы
				sockets[socket].close();
				delete sockets[socket];
			}
		//} catch(err) {}

		$.ajax({
	      type:"GET",
			  //cache : false,
			  url: link,
              timeout: 5000,
	      success:function(data){
                content.fadeTo(0, 1);
                disableRate();
                /* добавляем адрес следующего перехода в ссылку авторизации */
                $("#login-link").attr("href", "/login?next=" + pageUrl);
                $("#logout-link").attr("href", "/logout?next=" + pageUrl);
                var data2 = ('<div class="content">' + data + '</div>');
                $(data2).replaceAll('.content');
                scrollProcessingCheck();
                toggleCol();
                wsConnect();
                loader.hide();
                toggleTopMenu();
                tagBoxInit();
                editorInit();
                Comments();
	          }
	     });
        /* запрос сайдбара */
        if ( sidebarUrl != "" ) {
            $.ajax({
              type:"GET",
                  //cache : false,
                  url: sidebarUrl,
                  timeout: 5000,
                   success:function(data){
                    $(data).replaceAll(".sidebar-inner");
                   }
            });
        }
	   page = 1;

		};

function detectPageUrl() {
    var path = window.location.pathname.split('/');
	if (path.indexOf('cat') != -1) {
		catTab = $('a[href="/' + path[1] + '/' + path[2] + '"');
		catUrl = path[2];
        sidebarUrl = "/sidebar/" + catUrl;
	} else {
        catTab = "";
    }
    pageUrl = window.location.pathname;
    if ( pageUrl == '/' ) {
        sidebarUrl = "/sidebar/";
    }
	if ( path.indexOf('pop-all') || path.indexOf('pop-best') ) {
		pop = path[path.length-1];
	} else {
        pop = "";
    }
    return false;
}

function selectActiveTabs() {
    $(".menu").removeClass('active').parent().removeClass('active');
    if ( catTab.length > 0 ) {
        catTab.addClass('active').parent().addClass('active');
    } 
    if ( pop.length > 0 ) {
        $("#" + pop).addClass('active').parent().addClass('active');
    }
}

function toggleTopMenu() {
    if ( single_page || pageUrl == "/dashboard/my-posts" ) {
        $('.top-menu').hide();
    } else {
        $('.top-menu').show();
    }
}

function cloneComment( data ) {
    /* клонируем шаблон коммента и меняем значения на присланные из сокета */
	var comment = $(".sample_comment").clone();
			comment.removeClass('sample_comment');
			comment.attr('comment_id', data['id']);
			comment.attr('level', data['level']);
			comment.attr('parent', data['parent']);
			comment.css('margin-left', data['level']*25+'px');
			comment.find('.comment_text').html(data['text']);
			comment.find('.comment_user_avatar').children().attr('src', '/static' + data['avatar']);
			comment.find('.comment_username').html( data['author'] );
			comment.find('.comment-date').html( data['created'] );
    var last_child = "";
    var parent = "";
	if ( parseInt(comment['level']) > 0 ) {
		var p_str = "[comment_id="+parseInt(data['parent']) +"]" ;
		parent = $( p_str );
		last_child = $("[parent="+parseInt(data['parent']) +"]").last();
	} else {
		$(".comments").append( comment );
		comment.wrap('<ul><li></li></ul>');
		comment.css('display', 'block');
	}

	if (last_child.length > 0) {
		last_child = $( last_child ).parent('li');
		$( last_child ).after(comment);
		comment.wrap('<li></li>');
	} else {
		if ( parent.length > 0 ) {
			$( parent ).after(comment);
			comment.wrap('<ul><li></li></ul>');
		}
	}
	comment.css('display', 'block');
	//stubImgs();
}

function checkUserAuth() {
    /* проверка залогинен ли юзер */
	if ( $("#user_auth").length > 0 ) {
		userAuth = true;
	} else {
		userAuth = false }
}

function wsConnect() {
    /* соединение с вебсокетами */
	if ( $(".socket").length > 0 && userAuth ) {
        /* берём последнюю часть пути как адрес сокета */
        var socket_path = "ws://" + window.location.host + '/ws/';
        socket_path += decodeURIComponent(window.location.pathname).split('/').filter(Boolean).slice(-1)[0];

		var socket = new ReconnectingWebSocket(
			socket_path, null, {maxReconnectInterval: 2000, maxReconnectAttempts: 10});

		socket.onmessage = function(e) {

				var elem = JSON.parse(e.data);
				if ( elem['comment'] ) {
					cloneComment(elem);
				} else if (elem['post'] ) {
                    var postId = socket_path.split('-').filter(Boolean).slice(-1)[0];
                    //console.log(elem);
                    if ( parseInt($("#user_auth").attr('user')) == parseInt(elem['author']) ||
                       ( socket_path != "ws://192.168.1.70/ws/add-post" &&
                                String(elem['id']) == String(postId)) )  {
                        $("#post-link").attr('href', elem['url']);
                        $("#post-link").attr('url', elem['url'].slice(1));
                        $("#post-adding").hide();
                        $("#post-added-link").show();
                        loader.hide();
                    }
                }
		}

		socket.onopen = function() {
			//socket.send("hello world");
            /* добавляем сокет в массив чтобы потом отключиться */
			sockets[(window.location.pathname).split('/').filter(Boolean).slice(-1)[0]] = socket;
		}
		//socket.onclose = function() {
			//socket.send("disconnect");
		//}
		// Call onopen directly if socket is already open
		if (socket.readyState == WebSocket.OPEN) socket.onopen();
		}
	}

function BackForwardButtons() {
    /* при нажатии кнопок назад/вперёд в браузере */
	window.onpopstate = function(event) {
		var url = document.location.pathname;
        detectPageUrl();
        selectActiveTabs();
	  ChangePageNew(url);
	};

}

function HintPos() {
    /* автодополнения тэгов */
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
    /* копируем тэги из видимого поля в скрытое джанговское */
	$(".hidden_tags").val($("#tagBox").tagging( "getTags" ).toString());
}

function loadTags( tagBox ) {
    /* Загружаем тэги при редактировании поста в тэгбокс*/
    var tagsListElem = $("#tags_list");
    if ( tagsListElem.length ) {
        var tags_list = tagsListElem.attr('tags').replace(/'/g, '"');
        tags_list = JSON.parse(tags_list);
        for ( var tag in tags_list ) { 
            $( tagBox ).tagging( "add", tags_list[tag] );
        }; 
    }
}

function SelectHint() {
    /* при выборе подсказки при вводе тэгов */
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
    /* скрыть подсказки */
  $('.tt-menu').hide();
}

function Preview( files, el_id, url ) {
    /* предпросмотр картинок и гифок при создании/редактировании поста */
    if ( files ) {
        if ( files['name'].split('.').slice(-1)[0] == "webm" ) {
            var preview = $("#preview-template-webm").clone();
            preview.children().attr('src', window.URL.createObjectURL(files));
        } else {
            var preview = $("#preview-template").clone();
            preview.attr('src', window.URL.createObjectURL(files));
        }
    } else if ( url ) {
        if ( url.split('.').slice(-1)[0] == "webm" ) {
            var preview = $("#preview-template-webm").clone();
            preview.children().attr('src', $("#id_image_url").val());
        } else {
            var preview = $("#preview-template").clone();
            preview.attr('src', $("#id_image_url").val());
        }
    }


    preview.attr('id', 'preview');
    preview.attr('style', 'max-height: 300px;');
    $("#preview").replaceWith(preview);
  }

function editorInit() {
    
    var description = $('#id_description');
    var text = $('#id_text');
    if ( description .length || text.length ) {
        function imageLink(arr, action) {
        if ( action == "insert" ) {
           var index = arr.indexOf('insertLink');
            if (arr.indexOf('insertLink') != -1) {
                arr.splice(index + 1, 0, 'insertImage');
        } else if ( action == "remove") {
            var index = arr.indexOf('insertImage');
            if ( index != -1 ) {
                 arr.splice(index, 1);
                }
            }
        }
        return arr;
        }

        var toolbarButtons = [
        "bold", "italic", "underline", "strikeThrough", 
        "fontSize", "|", "align", "quote", "|", "-", "insertLink",
        "insertVideo", "|", "insertTable", "-", "undo", "redo",
        "clearFormatting"
        ];
        var toolbarButtonsMD = [
        "bold", "italic", "underline", "strikeThrough", 
        "fontSize", "|", "align", "quote", "|", "-", "insertLink",
        "insertVideo", "|", "insertTable", "-", "undo", "redo", "clearFormatting"
        ];
        var toolbarButtonsSM = [
        "bold", "italic", "underline", "strikeThrough", 
        "|", "align", "quote", "insertLink", "insertVideo", "undo", 
        "redo", "clearFormatting"
        ];
        var toolbarButtonsXS = [
        "align", "quote", "insertLink", "insertVideo", "undo", "redo", "clearFormatting"
        ];

        var params = {"fileUploadParams": {"csrfmiddlewaretoken": getCookie("csrftoken")},
            "imageMaxSize": 52428800, "inlineMode": false, 
            "imageUploadParams": {"csrfmiddlewaretoken": getCookie("csrftoken")},
            "charCounterMax": 500, "toolbarSticky": false,
            "placeholderText": "Короткое описание для главной", 
            "language": "ru",
            "imageResize": "false", "pasteDeniedTags": ["script"],
            "charCounterCount": true, "imagePasteProcess": "true",
            "fileUploadURL": "/froala_editorfile_upload/",
            "imageUploadURL": "/froala_editorimage_upload/", "toolbarInline": false,
            "iframe": false};
        params.toolbarButtons = toolbarButtons;
        params.toolbarButtonsMD = toolbarButtonsMD;
        params.toolbarButtonsSM = toolbarButtonsSM;
        params.toolbarButtonsXS = toolbarButtonsXS;

        var placeholderText = "Напишите что-нибудь или перетащите изображение";

        if ( description.length > 0 ) {
            params.toolbarButtons = imageLink(toolbarButtons, "remove");
            params.toolbarButtonsMD = imageLink(toolbarButtonsMD, "remove");
            params.toolbarButtonsSM = imageLink(toolbarButtonsSM, "remove");
            params.toolbarButtonsXS = imageLink(toolbarButtonsXS, "remove");
            $(description).froalaEditor(params);
        }
        if ( text.length > 0 ) {
            params.placeholderText = placeholderText;
            params.toolbarButtons = imageLink(toolbarButtons, "insert");
            params.toolbarButtonsMD = imageLink(toolbarButtonsMD, "insert");
            params.toolbarButtonsSM = imageLink(toolbarButtonsSM, "insert");
            params.toolbarButtonsXS = imageLink(toolbarButtonsXS, "insert");
            $(text).froalaEditor(params);
        }
    }
    

    
    return false;
}

function tagBoxInit() {
    var TagBox = $("#tagBox");
    
    if ( TagBox.length ) {
        var tagging_options = {
        "no-duplicate": true,
        "no-comma": false,
        "no-duplicate-callback": HideHint,
        "forbidden-chars-callback": null,
        "tag-on-blur": false,
        "no-spacebar": true,
        "case-sensitive": true,
        //"close-char": "X",
        "close-class": "material-icons close",
        "tag-class": "chip",
        "close-char": "close",
        "forbidden-chars": [],
        "forbidden-words": [],
        };

        TagBox.tagging( tagging_options);

        var taglist = new Bloodhound({
          datumTokenizer: Bloodhound.tokenizers.whitespace,
          queryTokenizer: Bloodhound.tokenizers.whitespace,
          prefetch: {
          url: '/tags.json',
          cache: false
          }
        });

        $('.type-zone').typeahead(null, {
          name: 'taglist',
          source: taglist,
          hint: true,
          highlight: true,
          minLength: 2,
          limit: 10
        });

        TagBox.on( "add:after", function (el, tagging){
            HintPos();
            CopyTags();
            TagBox.tagging( "emptyInput" );
            HideHint()
        } );

        TagBox.on( "remove:after", function (el, tagging){
            HintPos();
            CopyTags();
        } );

        $(document).on('click', '.tt-suggestion', function() {
            HideHint()
            TagBox.tagging( "add", $(this).text() );
            TagBox.tagging( "emptyInput" );
        });

        $(document).ready(function(){
            var post_image_url = $('#id_image_url');
            var preview = $('#preview');
            SelectHint();
            $('select').material_select();
            $('ul.tabs').tabs();
            loadTags( tagBox );
        });
    }
}

function playPause() {
    /* воспроизведение/пауза при клике на видео */
	$(document).on('click', 'video', function(e) {
		if ( this.paused ) {
			this.play();
		} else {
			this.pause();
		}
	});
 }
