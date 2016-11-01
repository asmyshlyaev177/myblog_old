from django.shortcuts import render
from blog.models import Post, myUser, Category, Tag
from django.utils.text import slugify
from blog.forms import SignupForm, MyUserChangeForm, AddPostForm
from django.http import (HttpResponseRedirect,
    HttpResponse,JsonResponse,HttpResponseNotFound)
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import deprecate_current_app
from django.views.decorators.debug import sensitive_post_parameters
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.core import serializers
from unidecode import unidecode
import json
from django.urls import reverse
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.vary import vary_on_headers
from django.views.decorators.cache import cache_control

from django.http import (
    HttpResponseBadRequest,
    HttpResponseServerError,
    HttpResponseForbidden,
)
from django.shortcuts import render
from django_summernote.settings import summernote_config, get_attachment_model

cat_list= Category.objects.all()

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

@login_required(login_url='/login')
@cache_page( 3 )
@vary_on_headers('X-Requested-With','Cookie')
@cache_control(max_age=3,private=True)
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


@login_required(redirect_field_name='next', login_url='/login')
@cache_page(2 )
@cache_control(max_age=2, private=True)
@vary_on_headers('X-Requested-With','Cookie')
def my_posts(request):
    if request.is_ajax() == True :
        template = 'dash-my-posts-ajax.html'
    else:
        template = 'dash-my-posts.html'
    post_list = Post.objects.filter(author=request.user.id)

    paginator = Paginator(post_list, 5)
    page = request.GET.get('page')

    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        #posts = paginator.page(paginator.num_pages)
        return HttpResponse('')

    return render(request, template, {'posts':posts,
                                              'cat_list': cat_list})

@login_required(redirect_field_name='next', login_url='/login')

@never_cache
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
            data.url = slugify(unidecode(data.title))
            url = data.get_absolute_url
            title = data.title
            tag_list = request.POST['hidden_tags'].split(',') # tags list
            data.save()
            j = True
            nsfw = data.private
            for i in tag_list:
                if nsfw == True:
                    tag_url = slugify(unidecode(i.lower()+"_nsfw"))
                    Tag.objects.get_or_create(name=i,
                                          url=tag_url,
                                          private=nsfw)
                    #tag = Tag.objects.get(name=i+"_nsfw")
                else:
                    tag_url = slugify(unidecode(i.lower()))
                    Tag.objects.get_or_create(name=i,
                                          url=tag_url )

                tag = Tag.objects.get(url=tag_url)

                data.tags.add(tag)
                if j:
                    if tag.url != "" and tag.url != None:
                        data.main_tag = tag.url
                    else:
                        data.main_tag = slugify(unidecode("Разное".lower()))
                    j = False

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
    with open('/root/myblog/myblog/blog/static/taglist.json', 'w') as out:
        out.write(json.dumps(data))

    return render(request, template, { 'form': form,
                                             'cat_list': cat_list})

@cache_page(30 )
@cache_control(max_age=30)
@vary_on_headers('X-Requested-With','Cookie')
def list(request, category=None, tag=None, pop=None):

    context = {}

    if request.is_ajax() == True :
        template = 'list_ajax.html'
    else:
        template = 'list.html'

    if tag:
        post_list= Post.objects.select_related("author", "category")\
            .prefetch_related('tags').filter(tags__url=tag)\
            .filter(status="P")#.order_by('-published')
        cat = Tag.objects.get(url=tag)      # переписать
        context['tag'] = cat
        if category:
            post_list = post_list.filter(category__slug=category)
            context['category'] = category

    else:
        if category:
            post_list= Post.objects.select_related("author", "category")\
                .prefetch_related('tags').filter(category__slug=category)\
                .filter(status="P")
        else:
            post_list = Post.objects.select_related("author", "category")\
                .prefetch_related('tags').filter(status="P")#.order_by('-published')

    if not request.user.is_authenticated:
        post_list = post_list.filter(private=False)
    #if pop:
    #    pass filter

    #post_list = post_list.filter(status="P").order_by('-published')
    paginator = Paginator(post_list, 3)
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

@cache_page(50)
@cache_control(max_age=50)
@vary_on_headers('X-Requested-With', 'Cookie')
def single_post(request,  tag, title, id):

    if request.is_ajax() == True :
        template = 'single_ajax.html'
    else:
        template = 'single.html'

    post = Post.objects.select_related("author", "category")\
        .prefetch_related('tags').get(pk=id)

    if post.private == True and not request.user.is_authenticated:
        return HttpResponseNotFound()

    return render(request, template,
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


@sensitive_post_parameters()
@csrf_protect
@login_required(redirect_field_name='next', login_url='/login')
@deprecate_current_app
@cache_page(2)
@cache_control(max_age=2, private=True)
@vary_on_headers('X-Requested-With','Cookie')
def password_change(request,
                    template_name='registration/password_change_form.html',
                    post_change_redirect=None,
                    password_change_form=PasswordChangeForm,
                    extra_context=None):
    if post_change_redirect is None:
        post_change_redirect = reverse('password_change_done')
    else:
        post_change_redirect = resolve_url(post_change_redirect)
    if request.is_ajax():
        template_name = 'registration/password_change_form-ajax.html'
    if request.method == "POST":
        form = password_change_form(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            # Updating the password logs out all other sessions for the user
            # except the current one.
            update_session_auth_hash(request, form.user)
            return HttpResponseRedirect(post_change_redirect)
    else:
        form = password_change_form(user=request.user)
    context = {
        'form': form,
        'title': _('Password change'),
        'cat_list': cat_list,
    }
    if extra_context is not None:
        context.update(extra_context)

    return TemplateResponse(request, template_name, context)
