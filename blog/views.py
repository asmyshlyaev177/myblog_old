from django.shortcuts import render
from blog.models import Post, myUser, Category, Tag
from django.utils.text import slugify
from blog.forms import SignupForm, MyUserChangeForm, AddPostForm
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

cat_list= Category.list()

@csrf_protect
def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/signup_success/')
    form = SignupForm()
    return render(request, 'registration/signup.html', { 'form': form })

def signup_success(request):
    return render(request, 'registration/signup_success.html')

@login_required
def dashboard(request):
    if request.method == 'POST':
        form = MyUserChangeForm(request.POST, request.FILES,
                                instance=request.user)
        if form.is_valid():
            form.save()
    else:
        form = MyUserChangeForm(instance=request.user)

    return render(request, 'dashboard.html', {'cat_list': cat_list,
                                              'form': form},
                                )

@login_required
def my_posts(request):
    posts = Post.objects.filter(author=request.user.id)
    return render(request, 'dash-my-posts.html', {'posts':posts,
                                              'cat_list': cat_list})

@login_required
def add_post(request):
    if request.method == 'POST':
        form = AddPostForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.save(commit=False)
            data.author = request.user
            data.url = slugify(data.title)
            url = data.get_absolute_url
            title = data.title
            data.save()
            return render(request, 'added-post.html',
                          {'url': url, 'title': title,
                           'cat_list':cat_list})
    form = AddPostForm()
    return render(request, 'add_post.html', { 'form': form,
                                             'cat_list': cat_list})

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
