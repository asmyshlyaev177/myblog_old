from django.shortcuts import render
from blog.models import Post, myUser, Category, Tag
from django.utils.text import slugify

cat_list= Category.list()

def Index(request):
    template = 'list.html'
    page_template = 'list_page.html'
    context = {
        'posts': Post.objects.select_related("author", "category")\
            .filter(status="P").order_by('-published'),
        'page_template': page_template,
        #'cat_list': Category.list()
        'cat_list': cat_list
    }

    if request.is_ajax():
        template = page_template
    return render(request, template, context )



def single_post(request, category, title, id):
    post = Post.objects.select_related("author").get(pk=id)
    return render(request, 'single.html',
                  {'post': post,
                   'category': category,
                  'cat_list': Category.list()})

def category(request, category):
    template = 'category.html'
    page_template = 'list_page.html'
    description = Category.objects.only("description")\
        .get(slug=category).description
    context = {
        'posts': Post.objects.select_related("author", "category")\
            .filter(status="P",category__name=category)\
            .order_by('-published'),
        'category': category,
        'description': description,
        'page_template': page_template,
        #'cat_list': Category.list()
        'cat_list': cat_list
        }
    if request.is_ajax():
        template = page_template

    return render(request, template, context)
