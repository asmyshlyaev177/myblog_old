# -*- coding: utf-8 -*-
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

from django.conf.urls import url, include
from django.contrib import admin
from blog import views
from django.views.static import serve
from django.conf import settings
from django.views.decorators.cache import cache_page
import debug_toolbar
from django.contrib.auth import views as auth_views

urlpatterns = [
    #url(r'^silk/', include('silk.urls', namespace='silk')),
    #url(r'^add-comment/(?P<postid>[-vi\d]+)/(?P<parent>[-vi/d]+)\/?',
    #    views.addComment, name='add-comment'),
    url(r'^add-comment/(?P<postid>[-vi\d]+)/(?P<parent>[-vi\d]+)\/?',
        views.addComment, name='add-comment'),
    url(r'^comments/(?P<postid>[-vi\d]+)\/?', views.comments, name='comments'),
    url(r'^tags.json\/?', views.tags, name='tags'),

    #url('login-social/', include('social.apps.django_app.urls', namespace='social')),
    url('login-social/', include('social_django.urls', namespace='social')),

    url(r'^froala_editor\/?', include('froala_editor.urls')),
    #url(r'^$', cache_page(60 * 15)(views.Index), name='Index'),
    url(r'^__debug__/', include(debug_toolbar.urls)),
    url(r'^admin\/?', admin.site.urls, name='myadmin'),
    url(r'^$', views.list, name='list'),
    url(r'^pop-(?P<pop>[-\w]+)\/?$', views.list, name='list_pop'),
    #url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    url(r'^add-post\/?$', views.add_post, name='add_post'),
    url(r'^edit-post-(?P<postid>[-vi\d]+)\/?$', views.edit_post, name='edit_post'),

    url(r'^signup\/?$', views.signup, name='signup'),
    url(r'^signup_success\/?$', views.signup_success, name='signup_success'),
    #url(r'^login\/?$', auth_views.login, name='login'),
    url(r'^login\/?$', views.login, name='login'),
    url(r'^dashboard\/?$', views.dashboard, name='dashboard'),
    url(r'^dashboard/my-posts\/?$', views.my_posts, name='my_posts'),
    url(r'^logout\/?$', auth_views.logout, name='logout'),
    url(r'^password_change\/?$', views.password_change, name='password_change'),
    url(r'^password_change/done\/?$', auth_views.password_change_done,
            name='password_change_done'),
    url(r'^password_reset\/?$', auth_views.password_reset,
        {'html_email_template_name': 'registration/password_reset_email.html'},
            name='password_reset'),
    url(r'^password_reset/done\/?$', auth_views.password_reset_done,
            name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})\/?$',
        auth_views.password_reset_confirm, name='password_reset_confirm'),
    url(r'^reset/done\/?$', auth_views.password_reset_done, name='password_reset_complete'),

    url(r'^rate/(?P<type>[-\w]+)/(?P<id>[-vi\d]+)-rate-(?P<vote>[-vi\d])\/?$',
            views.rate_elem, name='rate_elem'),

    url(r'^cat/(?P<category>([^\/]+))\/?$', views.list, name='category'),
    url(r'^cat/(?P<category>([^\/]+))/pop-(?P<pop>[-\w]+)\/?$', views.list, name='category_pop'),
    #url(r'^(?P<tag>((([-\w]+)?([-\W]+)?([-\w]+)?)+))\/?$', views.list, name='tag'),
    url(r'^(?P<tag>([^\/]+))\/?$', views.list, name='tag'),
    #url(r'^(?P<tag>[^/]+)\/?$', views.list, name='tag'),

    url(r'^(?P<tag>([^\/]+))/pop-(?P<pop>[-\w]+)\/?$', views.list, name='tag_pop'),

    #url(r'^(?P<tag>[-\w]+)/(?P<title>[-\w]+)-(?P<id>[-vi\d]+)\/?$',
    #        views.single_post, name='single_post'),
    url(r'^(?P<tag>([^\/]+)/(?P<title>([^\/]+))-(?P<id>[-vi\d]+))\/?$',
            views.single_post, name='single_post'),

    url(r'^media/(?P<path>.*)\/?$', serve,
            {'document_root': settings.MEDIA_ROOT}),

]
