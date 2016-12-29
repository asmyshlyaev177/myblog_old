from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from blog.models import Post, Category, Tag, myUser, Comment
from django import forms
from django.utils.text import slugify
from imagekit.admin import AdminThumbnail
from .forms import (UserCreationForm, UserChangeForm, MyUserChangeForm,
                    CommentForm)
from django.contrib.auth.models import Group
from django.contrib.auth.models import AbstractBaseUser
from froala_editor.widgets import FroalaEditor
from django.utils.html import format_html
from mptt.admin import MPTTModelAdmin

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
    fields = ('title', 'get_image', 'post_image', 'private',
              'description', 'text','author', 'category', 'tags',
                'published', 'url', 'main_tag','status')
    readonly_fields = ('get_image',)
    list_display = ('title', 'author', 'category',
                    'status','private','published')
    search_fields = ['title', 'description','text', 'tags__name', 'url']
    ordering = ['-status', '-published','title']
    show_full_result_count = True
    list_filter = ['category', 'status',
                    'created', 'published', 'private','edited']
    #url = Post.get_absolute_url()
    prepopulated_fields = {"url": ('title',)}


admin.site.register(Post, PostAdmin)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    orderinng = ['name',]


admin.site.register(Category, CategoryAdmin)


class TagAdminForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ('name', 'category',
                  'url', 'private', 'rateable', 'description')
        widgets = {
            'description': FroalaEditor(
                                options={'toolbarInline': False,
                                        'iframe': False,
                                        'toolbarSticky': False,
                                        'imageDefaultWidth': 800,
                                        'language': 'ru',
                                        'placeholderText': '''Напишите что-нибудь
                                        или перетащите изображение''',
                                        'imageMaxSize': 1024 * 1024 * 19,
                                        'pasteDeniedTags': ['script'],
                                        'imageEditButtons': [
                                            'imageAlign', 'imageRemove',
                                            '|', 'imageLink','linkOpen',
                                            'linkEdit', 'linkRemove', '-',
                                             'imageDisplay', 'imageStyle',
                                             'imageAlt', 'imageSize', 'html'
                                        ]},
                            plugins=('align', 'char_counter', 'code_beautifier',
                                     'code_view', 'colors', 'draggable', 'emoticons',
                                     'entities', 'file', 'font_family', 'font_size',
                                     'fullscreen', 'image_manager', 'image', 'inline_style',
                                     'line_breaker', 'link', 'lists', 'paragraph_format',
                                     'paragraph_style', 'quick_insert', 'quote', 'save', 'table',
                                     'url', 'video'),
            ),

        }

class TagAdmin(admin.ModelAdmin):
    form = TagAdminForm
    list_display = ('name', 'url','private', 'rateable', 'category')
    search_fields = ['name', 'url','description']
    readonly_fields = ('created',)
    list_filter = ['category','private', 'rateable']
    orderinng = ['name',]


admin.site.register(Tag, TagAdmin)

class CommentAdminForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("author", "text", "removed", "post")
        widgets = {
            'text': FroalaEditor(
                                options={'toolbarInline': False,
                                        'iframe': False,
                                        'toolbarSticky': False,
                                        'imageDefaultWidth': 800,
                                        'language': 'ru',
                                        'placeholderText': '''Напишите что-нибудь
                                        или перетащите изображение''',
                                        'imageMaxSize': 1024 * 1024 * 19,
                                        'pasteDeniedTags': ['script'],
                                        'imageEditButtons': [
                                            'imageAlign', 'imageRemove',
                                            '|', 'imageLink','linkOpen',
                                            'linkEdit', 'linkRemove', '-',
                                             'imageDisplay', 'imageStyle',
                                             'imageAlt', 'imageSize', 'html'
                                        ]},
                            plugins=('align', 'char_counter', 'code_beautifier',
                                     'code_view', 'colors', 'draggable', 'emoticons',
                                     'entities', 'file', 'font_family', 'font_size',
                                     'fullscreen', 'image_manager', 'image', 'inline_style',
                                     'line_breaker', 'link', 'lists', 'paragraph_format',
                                     'paragraph_style', 'quick_insert', 'quote', 'save', 'table',
                                     'url', 'video'),
            ),
        }

class CommentAdmin(admin.ModelAdmin):
    form = CommentAdminForm
    list_display = ( "author", "_text", "removed", "post", "created")
    def _text(self, obj):
        return format_html(obj.text)
    readonly_fields = ("created",)
    search_fields = ["text", "author__username", "post__title"]
    list_filter = ["created", "removed"]
    raw_id_fields = ("post",)
    ordering = ["created",]

admin.site.register(Comment, CommentAdmin)
