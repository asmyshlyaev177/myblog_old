from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from froala_editor.widgets import FroalaEditor

from blog.models import (Post, Category, Tag, MyUser, Comment)
from .forms import (UserCreationForm, MyUserChangeForm)


class UserAdmin(BaseUserAdmin):
    form = MyUserChangeForm
    add_form = UserCreationForm
    empty_value_display = '-empty-'
    list_display = ('username', 'email', 'date_joined', 'is_active')

    fieldsets = (
        (None, {'fields': ('username', 'get_avatar', 'avatar',
                           'email', 'is_active', 'moderated',
                           'is_staff', 'moderator',
                           'moderator_of_tags', 'moderator_of_categories')}),
    )

    # add_fieldsets = (
    #    (None, {
    #    'classes': ('wide',),
    #    'fields': ('username', 'email','password1','password2')}
    #        ),
    # )

    readonly_fields = ('date_joined', 'last_login', 'get_avatar')
    search_fields = ['email', 'username']
    ordering = ['username', 'email']
    show_full_result_count = True
    list_filter = ('is_active',
                   'is_staff')
    filter_horizontal = ()

    def get_avatar(self, obj):
        return obj.get_avatar()

    get_avatar.short_description = "Текущий аватар"


admin.site.register(MyUser, UserAdmin)


class PostAdmin(admin.ModelAdmin):
    empty_value_display = '-empty-'
    fields = ('title', 'get_image', 'post_image', 'private',
              'rateable', 'comments', 'locked',
              'description', 'text', 'author', 'category', 'tags',
              'published', 'url', 'main_tag', 'status')
    readonly_fields = ('get_image',)
    list_display = ('title', 'author', 'category',
                    'status', 'private', 'published')
    search_fields = ['title', 'description', 'text', 'tags__name', 'url']
    ordering = ['-status', '-published', 'title']
    show_full_result_count = True
    list_filter = ['category', 'status',
                   'created', 'published', 'private', 'edited']
    prepopulated_fields = {"url": ('title',)}


admin.site.register(Post, PostAdmin)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    orderinng = ['name', ]


admin.site.register(Category, CategoryAdmin)


class TagAdminForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ('name',
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
                             '|', 'imageLink', 'linkOpen',
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
    list_display = ('name', 'url', 'private', 'rateable')
    search_fields = ['name', 'url', 'description']
    readonly_fields = ('created',)
    list_filter = ['private', 'rateable']
    orderinng = ['name', ]


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
                             '|', 'imageLink', 'linkOpen',
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
    list_display = ("author", "_text", "removed", "post", "created")

    def _text(self, obj):
        return format_html(obj.text)

    readonly_fields = ("created",)
    search_fields = ["text", "author__username", "post__title"]
    list_filter = ["created", "removed"]
    raw_id_fields = ("post",)
    ordering = ["created", ]


admin.site.register(Comment, CommentAdmin)
