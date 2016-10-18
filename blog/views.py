from django.shortcuts import render
from blog.models import Post, myUser, Category, Tag
from django.utils.text import slugify
from blog.forms import SignupForm, MyUserChangeForm, AddPostForm
from django.http import HttpResponseRedirect, HttpResponse,JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.core import serializers
import json

from django.http import (
    HttpResponseBadRequest,
    HttpResponseServerError,
    HttpResponseForbidden,
)
from django.shortcuts import render
from django_summernote.settings import summernote_config, get_attachment_model

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
    if request.is_ajax() == True :
        template = 'dashboard-ajax.html'
    else:
        template = 'dashboard.html'

    if request.method == 'POST':
        form = MyUserChangeForm(request.POST, request.FILES,
                                instance=request.user)
        if form.is_valid():
            form.save()
    else:
        form = MyUserChangeForm(instance=request.user)

    return render(request, template, {'cat_list': cat_list,
                                              'form': form},
                                )

@login_required
def my_posts(request):
    posts = Post.objects.filter(author=request.user.id)
    return render(request, 'dash-my-posts.html', {'posts':posts,
                                              'cat_list': cat_list})

@login_required
def add_post(request):
    if request.is_ajax() == True :
        template = 'add_post-ajax.html'
    else:
        template = 'add_post.html'

    if request.method == 'POST':
        form = AddPostForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.save(commit=False)
            if request.user.moderated == False:
                data.status = "P"

            data.author = request.user
            data.url = slugify(data.title)
            url = data.get_absolute_url
            title = data.title
            tag_list = request.POST['hidden-tags_new'].split(',') # tags list
            data.save()
            for i in tag_list:
            	Tag.objects.get_or_create(name=i)
            	tag = Tag.objects.get(name=i)
            	data.tags.add(tag)
            data.save()
            #form.save_m2m()
            return render(request, 'added-post.html',
                          {'url': url, 'title': title,
                           'cat_list':cat_list})
    form = AddPostForm()

    #создаём файл со списком тэгов для выбора
    tags = Tag.objects.all().values()
    data = []
    for i in tags:
        #tag = {}
        #tag['id'] = i['id']
        #tag['name'] = i['name']
        data.append(i['name'])
    with open('c:\\django\\python3\\myblog\\blog\\static\\taglist.json', 'w') as out:
        out.write(json.dumps(data))

    return render(request, template, { 'form': form,
                                             'cat_list': cat_list})

def list(request, category=None, tag=None):

    context = {}

    if request.is_ajax() == True :
        template = 'list_ajax.html'
    else:
        template = 'list.html'

    if category:
        cat= Category.objects.get(slug=category)
        post_list= Post.objects.select_related("author", "category")\
            .prefetch_related('tags').filter(category__slug=category)\
                .filter(status="P")#.order_by('-published')
        context['category'] = cat
    elif tag:
        post_list= Post.objects.select_related("author", "category")\
            .prefetch_related('tags').filter(tags__id=tag)\
            .filter(status="P")#.order_by('-published')
        cat = Tag.objects.get(id=tag)
        context['tag'] = cat
    else:
        post_list = Post.objects.select_related("author", "category")\
            .prefetch_related('tags').filter(status="P")#.order_by('-published')

    #post_list = post_list.filter(status="P").order_by('-published')
    paginator = Paginator(post_list, 5)
    page = request.GET.get('page')

    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        #posts = paginator.page(paginator.num_pages)
        return HttpResponse('')
    context['posts'] = posts
    context['cat_list'] = cat_list
    context['page'] = page

    return render(request, template, context )


def single_post(request, category, title, id):
    post = Post.objects.select_related("author", "category")\
        .prefetch_related('tags').get(pk=id)
    return render(request, 'single.html',
                  {'post': post,
                  'cat_list': Category.list()})

def upload_attachment(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Only POST method is allowed')

    if summernote_config['attachment_require_authentication']:
        if not request.user.is_authenticated():
            return HttpResponseForbidden('Only authenticated users are allowed')

    if not request.FILES.getlist('files'):
        return HttpResponseBadRequest('No files were requested')

    try:
        attachments = []

        for file in request.FILES.getlist('files'):

            # create instance of appropriate attachment class
            klass = get_attachment_model()
            attachment = klass()

            attachment.file = file
            attachment.name = file.name

            if file.size > summernote_config['attachment_filesize_limit']:
                return HttpResponseBadRequest(
                    'File size exceeds the limit allowed and cannot be saved'
                )

            # remove unnecessary CSRF token, if found
            request.POST.pop("csrfmiddlewaretoken", None)
            kwargs = request.POST
            # calling save method with attachment parameters as kwargs
            attachment.save(**kwargs)

            attachments.append(attachment)

        return render(request, 'upload_attachment.json', {
            'attachments': attachments,
        })
    except IOError:
        return HttpResponseServerError('Failed to save attachment')
