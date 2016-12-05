from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from blog.models import Post, Category, Tag, myUser
from django import forms
from django.utils.text import slugify
from imagekit.admin import AdminThumbnail
from .forms import UserCreationForm, UserChangeForm, MyUserChangeForm
from django.contrib.auth.models import Group
from django.contrib.auth.models import AbstractBaseUser


class UserAdmin(BaseUserAdmin):
    form = MyUserChangeForm
    add_form = UserCreationForm
    empty_value_display = '-empty-'
    list_display = ('username', 'email', 'date_joined', 'is_active')

    fieldsets = (
        (None, {'fields': ('username','get_avatar','avatar',
                           'email','password','is_active','moderated',
                           'is_it_staff', 'is_it_superuser')}),
    )

    #add_fieldsets = (
    #    (None, {
    #    'classes': ('wide',),
    #    'fields': ('username', 'email','password1','password2')}
    #        ),
    #)

    readonly_fields = ('date_joined', 'last_login','get_avatar')
    search_fields = ['email', 'username']
    ordering = ['username', 'email']
    show_full_result_count = True
    list_filter = ('is_active',
                       'is_it_staff', 'is_it_superuser')
    filter_horizontal = ()

admin.site.register(myUser, UserAdmin)
admin.site.unregister(Group)

class PostAdmin(admin.ModelAdmin):
    empty_value_display = '-empty-'
    fields = ('title', 'get_image', 'post_image', 'description', 'text',
               'author', 'category', 'tags',
                'published', 'url', 'main_tag','status')
    readonly_fields = ('get_image',)
    list_display = ('title', 'author', 'category',
                    'status','published')
    search_fields = ['title', 'description','text', 'tag', 'url']
    ordering = ['-status', '-published','title']
    show_full_result_count = True
    list_filter = ['category', 'status',
                    'created', 'published', 'edited']
    #url = Post.get_absolute_url()
    prepopulated_fields = {"url": ('title',)}


admin.site.register(Post, PostAdmin)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    orderinng = ['name',]


admin.site.register(Category, CategoryAdmin)

class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'url','private', 'rateable', 'category', 'description')
    orderinng = ['name',]
    
admin.site.register(Tag, TagAdmin)
