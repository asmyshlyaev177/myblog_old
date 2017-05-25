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

import debug_toolbar
from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.sitemaps.views import index, sitemap
from django.views.static import serve
from blog import views
from blog.sitemap import BlogSitemap

sitemaps = {'posts': BlogSitemap()}

urlpatterns = [
    # url(r'^silk/', include('silk.urls', namespace='silk')),
    url(r'^clear-cache\/?', views.clear_cache, name='clear_cache'),

    url(r'^sitemap\.xml$', index, {'sitemaps': sitemaps}),
    url(r'^sitemap-(?P<section>.+)\.xml$', sitemap, {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap'),

    # url(r'^test\/?$', views.test_view, name='test_view'),

    url(r'sidebar/(?P<category>([^\/]+))?\/?', views.Sidebar.as_view(), name='sidebar'),
    url(r'^add-comment/(?P<postid>[-vi\d]+)/(?P<parent>[-vi\d]+)\/?',
        views.AddComment.as_view(), name='add-comment'),
    url(r'^comments/(?P<postid>[-vi\d]+)\/?', views.Comments.as_view(), name='comments'),
    url(r'^tags.json\/?', views.Tags.as_view(), name='tags'),

    url('login-social/', include('social_django.urls', namespace='social')),

    url(r'^froala_editor\/?', include('froala_editor.urls')),
    url(r'^__debug__/', include(debug_toolbar.urls)),
    url(r'^admin\/?', admin.site.urls, name='myadmin'),
    url(r'^$', views.List.as_view(), name='list'),
    # url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    url(r'^add-post\/?$', views.AddPost.as_view(), name='add_post'),
    url(r'^post-saved(?P<pk>[-vi\d]+)?\/?$', views.PostSaved.as_view(), name='edited_post'),
    url(r'^edit-post-(?P<pk>[-vi\d]+)\/?$', views.EditPost.as_view(), name='edit_post'),

    url(r'^signup\/?$', views.Signup.as_view(), name='signup'),
    url(r'^signup_success\/?$', views.SignupSuccess.as_view(), name='signup_success'),
    url(r'^login\/?$', views.Login.as_view(), name='login'),
    url(r'^dashboard\/?$', views.Dashboard.as_view(), name='dashboard'),
    url(r'^dashboard/my-posts\/?$', views.MyPosts.as_view(), name='my_posts'),
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
    url(r'^complain/(?P<type>[-\w]+)/(?P<objid>[-vi\d]+)/(?P<reason>([^\/]+))\/?$',
        views.complain_elem, name='complain'),

    url(r'^pop-(?P<pop>[-\w]+)\/?$', views.ListPop.as_view(), name='list_pop'),
    url(r'^cat/(?P<category>([^\/]+))\/?$', views.ListCat.as_view(), name='category'),
    url(r'^cat/(?P<category>([^\/]+))/pop-(?P<pop>[-\w]+)\/?$', views.ListCatPop.as_view(), name='category_pop'),
    url(r'^tag/(?P<tag>([^\/]+))\/?$', views.ListTag.as_view(), name='tag'),

    url(r'^tag/(?P<tag>([^\/]+))/pop-(?P<pop>[-\w]+)\/?$', views.ListTagPop.as_view(), name='tag_pop'),

    # url(r'^(?P<tag>([^\/]+))/(?P<title>([^\/]+))-(?P<id>([-vi\d]+))\/?$',
    #        views.single_post, name='single_post'),
    url(r'^post/(?P<tag>([-\w]+))/(?P<title>([-\w]+))-(?P<pk>([-vi\d]+))\/?$',
        views.SinglePost.as_view(), name='single_post'),

    url(r'^media/(?P<path>.*)\/?$', serve,
        {'document_root': settings.MEDIA_ROOT}),

]
