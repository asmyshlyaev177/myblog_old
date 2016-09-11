"""myblog URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url,include
from django.contrib import admin
from blog import views
from blog.views import Index
from django.views.static import serve
from django.conf import settings
from django.views.decorators.cache import cache_page

urlpatterns = [

    #url(r'^$', cache_page(60 * 15)(views.Index), name='Index'),
    url(r'^$', views.Index, name='Index'),
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    url(r'^(?P<category>[-\w]+)/$', views.category, name='category'),
    url(r'^(?P<category>[-\w]+)/(?P<title>[-\w]+)-(?P<id>[-vi\d]+)/',
            views.single_post, name='single_post'),
    #url(r'^(?P<category>[-\w]+)/(?P<title>[-\w]+)-(?P<id>[-vi\d]+)/',
    #        cache_page(60 * 15)(views.single_post), name='single_post'),
    url(r'^media/(?P<path>.*)$', serve,
            {'document_root': settings.MEDIA_ROOT}),
    #url(r'^media/(?P<path>.*)$', cache_page(60 *15)(serve),
    #        {'document_root': settings.MEDIA_ROOT}),
    url(r'^admin/', admin.site.urls, name='myadmin'),
]
