from django.contrib import admin
from blog.models import Post, Category, Tag, User
from django import forms
from django.utils.text import slugify
from imagekit.admin import AdminThumbnail

class UserAdmin(admin.ModelAdmin):
    empty_value_display = '-empty-'
    fields = ('username', 'email')
    list_display = ('username', 'email', 'date_joined', 'is_active')
    readonly_fields = ('date_joined', 'last_login')
    search_fields = ['email', 'username']
    ordering = ['username', 'email']
    show_full_result_count = True

admin.site.register(User, UserAdmin)

class PostAdmin(admin.ModelAdmin):
    empty_value_display = '-empty-'
    fields = ('title', 'get_image', 'post_image', 'description', 'text',
               'author', 'category',
                'published', 'url', 'status')
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

admin.site.register(Tag)
