# -*- coding: utf-8 -*-
from django.shortcuts import render
from blog.models import (Post, Category, Tag, Comment)
#from slugify import slugify
from django.utils.text import slugify
from blog.forms import SignupForm, MyUserChangeForm, AddPostForm, CommentForm
from django.http import (HttpResponseRedirect,
                        HttpResponse, HttpResponseNotFound)
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json
from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.vary import vary_on_headers
from django.views.decorators.cache import cache_control
from django.core.cache import cache
from blog.tasks import addPost, Rate, commentImage
from django.contrib.auth.views import (login as def_login,
                                password_change as def_password_change)

cat_list = Category.objects.all()


@cache_page(3)
@cache_control(max_age=3)
@vary_on_headers('X-Requested-With', 'Cookie')
def login(request, *args, **kwargs):
    if request.is_ajax():
        template = 'registration/login_ajax.html'
    else:
        template = 'registration/login.html'

    return def_login(request, *args, **kwargs, template_name=template,
                                extra_context={'cat_list': cat_list})


@cache_page(3)
@cache_control(max_age=3)
def comments(request, postid):
    post = Post.objects.get(id=postid)

    cache_str = "comment_" + str(postid)
    if cache.ttl(cache_str):
        comments = cache.get(cache_str)
    else:
        comments = Comment.objects.filter(post=post)\
            .select_related("author")\
            .prefetch_related('ratingcomment_set')
        cache.set(cache_str, comments, timeout=300)

    template = 'comments-ajax.html'
    return render(request, template,
                  {'comments': comments})


@never_cache
@login_required(login_url='/login')
def addComment(request, postid, parent=0):
    if request.method == "POST":
        comment_form = CommentForm(request.POST, request.FILES)
        if comment_form.is_valid():
            parent_comment = int(parent)
            comment = comment_form.save(commit=False)
            comment.author = request.user
            comment.post = Post.objects.get(id=postid)
            if parent_comment != 0:
                comment.parent = Comment.objects.get(id=parent_comment)
            comment.save()
            commentImage.delay(comment.id)

            return HttpResponse("OK")
    else:
        pass


@never_cache
def tags(request):
    # tags = Tag.objects.all().values().cache()

    if cache.ttl("taglist"):
        data = cache.get("taglist")
    else:
        tags = Tag.objects.all().values("name")
        data = []
        for i in tags:
            data.append(i['name'])
        cache.set("taglist", data, timeout=None)

    return HttpResponse(json.dumps(data), content_type="application/json")


@csrf_protect
@cache_page(3)
@cache_control(max_age=3)
@vary_on_headers('X-Requested-With', 'Cookie')
def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/signup_success/')
    form = SignupForm()
    return render(request, 'registration/signup.html', {'form': form,
                                                        'cat_list': cat_list})


def signup_success(request):
    return render(request, 'registration/signup_success.html')


@login_required(login_url='/login')
# @cache_page( 5 )
# @vary_on_headers('X-Requested-With','Cookie')
# @cache_control(max_age=5,private=True)
# @never_cache
@never_cache
def dashboard(request):
    if request.is_ajax():
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
# @cache_page(5 )
# @cache_control(max_age=5, private=True)
# @vary_on_headers('X-Requested-With','Cookie')
@never_cache
def my_posts(request):
    if request.is_ajax():
        template = 'dash-my-posts-ajax.html'
    else:
        template = 'dash-my-posts.html'
    # post_list = Post.objects.filter(author=request.user.id).cache()
    post_list = Post.objects.filter(author=request.user.id)

    paginator = Paginator(post_list, 5)
    page = request.GET.get('page')

    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        # posts = paginator.page(paginator.num_pages)
        return HttpResponse('')

    return render(request, template, {'posts': posts,
                                              'cat_list': cat_list})


@never_cache
def edit_post(request, postid):
    template = 'edit_post.html'
    post = Post.objects.get(id=postid)

    if request.method == 'POST':
        form = AddPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            data = form.save(commit=False)
            if request.user.moderated:
                moderated = True
            else:
                moderated = False
            ##data.author = request.user
            data.url = slugify(data.title, allow_unicode=True)
            title = data.title
            tag_list = request.POST['hidden_tags'].split(',')  # tags list

            have_new_tags = False
            data.save()
            post_id = data.id
            addPost.delay(post_id, tag_list, moderated)

            return render(request, 'added-post.html',
                          {'title': title,
                           'cat_list': cat_list})

    else:
        form = AddPostForm(instance=post)

    tags_list = []
    for i in post.tags.all():
        tags_list.append(i.name)
    return render(request, template,
                {'form': form, 'post': post,
                 'cat_list': cat_list, 'tags_list': tags_list})


@login_required(redirect_field_name='next', login_url='/login')
@cache_page(3)
@cache_control(max_age=3)
@vary_on_headers('X-Requested-With', 'Cookie')
def add_post(request):
    if request.is_ajax():
        template = 'add_post-ajax.html'
    else:
        template = 'add_post.html'

    if request.method == 'POST':
        form = AddPostForm(request.POST, request.FILES)
        if form.is_valid():

            data = form.save(commit=False)
            if request.user.moderated:
                moderated = True
            else:
                moderated = False

            data.author = request.user
            data.url = slugify(data.title, allow_unicode=True)
            title = data.title
            tag_list = request.POST['hidden_tags'].split(',')  # tags list

            have_new_tags = False
            data.save()
            post_id = data.id
            addPost.delay(post_id, tag_list, moderated)

            return render(request, 'added-post.html',
                          {'title': title,
                           'cat_list': cat_list})

    form = AddPostForm()

    return render(request, template, {'form': form,
                                             'cat_list': cat_list})


@login_required(redirect_field_name='next', login_url='/login')
@never_cache
def rate_elem(request, type, id, vote):
    if request.method == 'POST':

        user = request.user
        uv = cache.get('user_votes_' + str(user.id))
        votes_count = user.votes_count

        if ((uv is None and votes_count != "B") or
        (uv['votes'] > 0 and votes_count != "B")):
            date_joined = str(user.date_joined.strftime('%Y_%m_%d'))
            Rate.delay(user.id, date_joined, votes_count, type, id, vote)
        else:
            return HttpResponse("no votes")

        return HttpResponse("accepted")


# @cache_page(3)
# @cache_control(max_age=3)
# @vary_on_headers('X-Requested-With', 'Cookie')
@never_cache
def list(request, category=None, tag=None, pop=None):
    hot_rating = 3
    context = {}

    if request.is_ajax():
        template = 'list_ajax.html'
    else:
        template = 'list.html'

    user_known = False
    if request.user.is_authenticated:
        user_known = True
        # post_list = post_list.filter(private=False)

    if tag:
        cache_str_tag = "post_list_" + str(tag) + "_" + str(user_known)\
                                                        + "_" + str(pop)
        if cache.ttl(cache_str_tag):
            post_list = cache.get(cache_str_tag)
        else:
            if not user_known:
                post_list = Post.objects.filter(tags__url=tag)\
                            .filter(status="P").filter(private=False)\
                            .select_related("category", "author")\
                            .prefetch_related('tags', 'ratingpost_set')
            else:
                post_list = Post.objects.filter(tags__url=tag)\
                            .filter(status="P")\
                            .select_related("category", "author")\
                            .prefetch_related('tags', 'ratingpost_set')
            if pop == "best":
                post_list = post_list.filter(ratingpost__rating__gte=hot_rating)
                cache.set(cache_str_tag, post_list, 300)
            else:
                cache.set(cache_str_tag, post_list, 1800)

    elif category:
        cache_str_cat = "post_list_" + str(category.lower())\
            + "_" + str(user_known) + "_" + str(pop)
        if cache.ttl(cache_str_cat):
            post_list = cache.get(cache_str_cat)
        else:
            if not user_known:
                post_list = Post.objects.filter(category__slug=category)\
                            .filter(status="P").filter(private=False)\
                            .select_related("category", "author")\
                            .prefetch_related('tags', 'ratingpost_set')
            else:
                post_list = Post.objects.filter(category__slug=category)\
                            .filter(status="P")\
                            .select_related("category", "author")\
                            .prefetch_related('tags', 'ratingpost_set')
            if pop == "best":
                post_list = post_list.filter(ratingpost__rating__gte=hot_rating)
                cache.set(cache_str_cat, post_list, 300)
            else:
                cache.set(cache_str_cat, post_list, 1800)

    else:
        cache_str = "post_list_" + str(user_known) + "_" + str(pop)
        if cache.ttl(cache_str):
            post_list = cache.get(cache_str)
        else:
            if not user_known:
                post_list = Post.objects\
                            .filter(status="P").filter(private=False)\
                            .select_related("category", "author")\
                            .prefetch_related('tags', 'ratingpost_set')
            else:
                post_list = Post.objects\
                            .filter(status="P")\
                            .select_related("category", "author")\
                            .prefetch_related('tags', 'ratingpost_set')
            if pop == "best":
                post_list = post_list.filter(ratingpost__rating__gte=hot_rating)
                cache.set(cache_str, post_list, 300)
            else:
                cache.set(cache_str, post_list, 1800)

    paginator = Paginator(post_list, 3)
    page = request.GET.get('page')

    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        # posts = paginator.page(paginator.num_pages)
        posts = None
        # return HttpResponse('')
    context['posts'] = posts
    context['cat_list'] = cat_list
    context['page'] = page

    return render(request, template, context)


# @cache_page(3)
# @cache_control(max_age=3)
# @vary_on_headers('X-Requested-With', 'Cookie')
@never_cache
def single_post(request, tag, title, id):

    if request.is_ajax():
        template = 'single_ajax.html'
    else:
        template = 'single.html'

    # post = Post.objects.select_related("author", "category")\
    # .prefetch_related('tags').cache().get(pk=id)

    cache_str = "post_single_" + str(id)
    if cache.ttl(cache_str):
        post = cache.get(cache_str)
    else:
        post = Post.objects.select_related("category")\
            .prefetch_related('tags', 'ratingpost_set').get(pk=id)
        cache.set(cache_str, post, 1800)

    if post.private and not request.user.is_authenticated:
        return HttpResponseNotFound()

    comment_form = CommentForm()

    # comments = Comment.objects.filter(post=post)

    comments = Comment.objects.filter(post=post)

    return render(request, template,
                  {'post': post,
                  'cat_list': cat_list, 'comment_form': comment_form,
                  'comments': comments})


@cache_page(3)
@cache_control(max_age=3)
@vary_on_headers('X-Requested-With', 'Cookie')
def password_change(request, *args, **kwargs):
    if request.is_ajax():
        template = 'registration/password_change_form-ajax.html'
    else:
        template = 'registration/password_change_form.html'

    return def_password_change(request, *args, **kwargs,
                            template_name=template,
                            extra_context={'cat_list': cat_list})
