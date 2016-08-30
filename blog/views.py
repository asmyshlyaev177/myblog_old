from django.shortcuts import render
from blog.models import Post, User, Category, Tag

def index(request):
    posts = Post.objects.filter(status="P")
    return render(request, 'list.html', {'posts': posts} )

def single_post(request, category, title, id):
    post = Post.objects.get(pk=id)
    return render(request, 'single.html', {'post': post })

#def category_list(request):
