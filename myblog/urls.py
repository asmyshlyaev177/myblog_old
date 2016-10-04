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
import debug_toolbar
from django.contrib.auth import views as auth_views

urlpatterns = [

    #url(r'^$', cache_page(60 * 15)(views.Index), name='Index'),
    url(r'^__debug__/', include(debug_toolbar.urls)),
    url(r'^admin/', admin.site.urls, name='myadmin'),
    url(r'^$', views.Index, name='Index'),
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    url(r'^add-post/$', views.add_post, name='add_post'),

    url(r'^signup/', views.signup, name='signup'),
    url(r'^signup_success/$', views.signup_success, name='signup_success'),
    url(r'^login/', auth_views.login, name='login'),
    url(r'^dashboard/$', views.dashboard, name='dashboard'),
    url(r'^dashboard/my-posts/$', views.my_posts, name='my_posts'),
    url(r'^logout/', auth_views.logout, name='logout'),
    url(r'^password_change/$', auth_views.password_change, name='password_change'),
    url(r'^password_change/done/$', auth_views.password_change_done,
            name='password_change_done'),
    url(r'^password_reset/$', auth_views.password_reset,
        { 'html_email_template_name': 'registration/password_reset_email.html'},
            name='password_reset'),
    url(r'^password_reset/done/$', auth_views.password_reset_done,
            name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm, name='password_reset_confirm'),
    url(r'^reset/done/$', auth_views.password_reset_done, name='password_reset_complete'),

    url(r'^(?P<category>[-\w]+)/$', views.category, name='category'),
    url(r'^(?P<category>[-\w]+)/(?P<title>[-\w]+)-(?P<id>[-vi\d]+)/',
            views.single_post, name='single_post'),
    url(r'^media/(?P<path>.*)$', serve,
            {'document_root': settings.MEDIA_ROOT}),


]
