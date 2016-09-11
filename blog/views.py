from django.shortcuts import render
from blog.models import Post, myUser, Category, Tag
from django.utils.text import slugify

def Index(request):
    template = 'list.html'
    page_template = 'list_page.html'
    context = {
        'posts': Post.objects.filter(status="P").order_by('-published'),
        'page_template': page_template,
        'categories': Category.objects.all(),
        'cat_list': Category.list()
    }

    if request.is_ajax():
        template = page_template
    return render(request, template, context )



def single_post(request, category, title, id):
    post = Post.objects.get(pk=id)
    return render(request, 'single.html',
                  {'post': post,
                   'category': category,
                  'cat_list': Category.list()})

def category(request, category):
    template = 'category.html'
    page_template = 'list_page.html'
    cat_description = Category.objects.get(slug=category)
    context = {
        'posts': Post.objects.filter(status="P",category__name=category)\
        .order_by('-published'),
        'category': category,
        'description': cat_description.description,
        'page_template': page_template,
        'cat_list': Category.list()
        }
    if request.is_ajax():
        template = page_template

    return render(request, template, context)
