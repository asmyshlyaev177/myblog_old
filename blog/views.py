# -*- coding: utf-8 -*-
from django.shortcuts import render
from blog.models import (Post, Category, Tag, Comment, myUser, Complain)
#  from slugify import slugify
from django.utils.text import slugify
from blog.forms import SignupForm, MyUserChangeForm, AddPostForm, CommentForm
from django.http import (HttpResponseRedirect, HttpResponseForbidden,
                        HttpResponse, HttpResponseNotFound)
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json, sys, os, datetime
from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.vary import vary_on_headers
from django.views.decorators.cache import cache_control
from django.core.cache import cache
from blog.tasks import addPost, Rate, commentImage, ComplainObj
from django.contrib.auth.views import (login as def_login,
                                password_change as def_password_change)

hot_rating = 3

@never_cache
def test_view(request):
    """
    Тестовая вьюшка для отдельного поста
    """

    template = 'test.html'

    context = {}
    context['post'] = Post.objects.get(id=6520)
    context['cat_list'] = get_cat_list()

    return render(request, template, context)

def clear_cache(request):
    """
    Внешний скрипт для админки для очистки кэша
    """
    if request.user.is_superuser:
        os.system("/root/myblog/myblog/clear_cache.sh")
        return HttpResponseRedirect('/admin/')
    else:
        return HttpResponseForbidden()


def get_good_posts(category=None, private=None):
    """
    Популярные посты для сайдбара
    """
    cache_str = "good_posts_" + str(category) + "_" + str(private)
    if cache.ttl(cache_str):
        posts = cache.get(cache_str)
    else:
        cur_date = datetime.datetime.now()
        delta = datetime.timedelta(days=14)
        start_date = cur_date - delta
        posts = Post.objects\
                .filter(status="P")\
                .filter(rating__gte=0)\
                .order_by("-rating")\
                .prefetch_related("tags", "category", "author", "main_tag")\
                .only("id", "title", "description", "url", "category", "post_image",
                    "main_tag", "main_image_srcset", "private", "rating", "created")
                #.filter(published__range=(start_date, cur_date))\
        if category:
            posts = posts.filter(category__slug=category)
        if not private:
            posts = posts.exclude(private=True)
        posts = posts[0:4]
        cache.set(cache_str, posts, 7200)
    return posts


def sidebar(request, category=None):
    """
    Вьюшка для сайдбара
    """
    template = "sidebar.html"
    if request.user.is_authenticated:
        user_known = True
    else:
        user_known = False
    good_posts = get_good_posts(category=category, private=user_known)
    return render(request, template, {'good_posts': good_posts, 'category': category})


def get_cat_list():
    """
    Лист категорий
    """
    return cache.get_or_set("cat_list", Category.objects.all(), 36000)


@cache_page(3600)
@cache_control(max_age=3600)
@vary_on_headers('X-Requested-With', 'Cookie')
def login(request, *args, **kwargs):
    """Логин"""
    if request.is_ajax():
        template = 'registration/login_ajax.html'
    else:
        template = 'registration/login.html'

    return def_login(request, *args, **kwargs, template_name=template,
                                extra_context={'cat_list': get_cat_list()})


@cache_page(7200)
@cache_control(max_age=7200)
def comments(request, postid):
    """ 
    Комментарии для поста
    """
    cache_str = "comment_" + str(postid)
    query = Comment.objects.filter(post=postid)\
            .prefetch_related("author")
    comments = cache.get_or_set(cache_str, query, 7200)

    template = 'comments-ajax.html'
    return render(request, template,
                  {'comments': comments})


@never_cache
@login_required(login_url='/login')
def addComment(request, postid, parent=0):
    """
    Добавление поста
    """
    if request.method == "POST":
        comment_form = CommentForm(request.POST, request.FILES)
        if comment_form.is_valid():
            parent_comment = int(parent)
            comment = comment_form.save(commit=False)
            comment.author = request.user
            comment.post = Post.objects.only('id').get(id=postid)
            if parent_comment != 0:
                comment.parent = Comment.objects.only('id').get(id=parent_comment)
            comment.save()
            commentImage.delay(comment.id)

            return HttpResponse("OK")
    else:
        pass


@never_cache
def tags(request):
    """
    Список тэгов для добавления/редактирования поста
    """
    # tags = Tag.objects.all().values().cache()
    query = Tag.objects.all().values("name")
    tags = cache.get_or_set("taglist", query, 36000)
    data = []
    for tag in tags:
        data.append(tag['name'])

    return HttpResponse(json.dumps(data), content_type="application/json")


@csrf_protect
@cache_page(7200)
@cache_control(max_age=7200)
@vary_on_headers('X-Requested-With')
def signup(request):
    """Регистрация"""
    if request.is_ajax():
        template = 'registration/signup-ajax.html'
    else:
        template = 'registration/signup.html'
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/signup_success/')
    form = SignupForm()
    return render(request, template, {'form': form,
                                                'cat_list': get_cat_list()})


def signup_success(request):
    """Заглушка при успешной регистрации"""
    return render(request, 'registration/signup_success.html')


@login_required(login_url='/login')
# @cache_page( 5 )
# @vary_on_headers('X-Requested-With','Cookie')
# @cache_control(max_age=5,private=True)
# @never_cache
@never_cache
def dashboard(request):
    """
    Данные о пользователи, мэйл, аватар и т.д.
    """
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

    return render(request, template, {'cat_list': get_cat_list(),
                                              'form': form},
                                                            )


@login_required(redirect_field_name='next', login_url='/login')
# @cache_page(5 )
# @cache_control(max_age=5, private=True)
# @vary_on_headers('X-Requested-With','Cookie')
@never_cache
def my_posts(request):
    """
    Страница с постами пользователя
    """
    if request.is_ajax():
        template = 'dash-my-posts-ajax.html'
    else:
        template = 'dash-my-posts.html'
    # post_list = Post.objects.filter(author=request.user.id).cache()
    post_list = Post.objects.prefetch_related()\
                .select_related().filter(author=request.user.id)

    paginator = Paginator(post_list, 5)
    page = request.GET.get('page')

    try:
        posts = paginator.page(page).object_list
    except PageNotAnInteger:
        posts = paginator.page(1).object_list
    except EmptyPage:
        posts = None
    
    context = {}
    context['posts'] = posts
    context['cat_list'] = get_cat_list()

    if not posts and page:
        return HttpResponse('last_page')
    else:
        return render(request, template, context)


@never_cache
def edit_post(request, postid):
    """
    Редактирование постов
    """
    if request.is_ajax():
        template = 'edit_post-ajax.html'
    else:
        template = 'edit_post.html'
    post = Post.objects.select_related().prefetch_related().get(id=postid)

    if request.user.is_authenticated:
        if request.user.is_superuser\
                or request.user.is_moderator(post)\
                or request.user.id == post.author.id:

            if request.method == 'POST':
                form = AddPostForm(request.POST, request.FILES, instance=post)
                if form.is_valid():
                    data = form.save(commit=False)
                    if request.user.moderated:
                        moderated = True
                    else:
                        moderated = False
                    data.url = slugify(data.title, allow_unicode=True)
                    title = data.title
                    tag_list = request.POST['hidden_tags'].split(',')  # tags list

                    have_new_tags = False
                    data.save()
                    post_id = data.id
                    group = "edit-post-" + str(post_id)
                    addPost.apply_async(args=[post_id, tag_list, moderated], kwargs={'group': group}, countdown=7)

                    return render(request, 'added-post.html',
                                  {'title': title,
                                   'cat_list': get_cat_list()})

            else:
                form = AddPostForm(instance=post)

            tags_list = []
            for tag in post.tags.all():
                tags_list.append(tag.name)
            return render(request, template,
                        {'form': form, 'post': post,
                         'cat_list': get_cat_list(), 'tags_list': tags_list})

    else:
        return HttpResponseForbidden()


@login_required(redirect_field_name='next', login_url='/login')
@cache_page(9)
@cache_control(max_age=9)
@vary_on_headers('X-Requested-With')
def add_post(request):
    """
    Добавление постов
    """
    if request.is_ajax():
        template = 'add_post-ajax.html'
    else:
        template = 'add_post.html'

    if request.method == 'POST':
        form = AddPostForm(request.POST, request.FILES)
        form.data['status'] = 'D'

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

            data.save()
            post_id = data.id
            #addPost.delay(post_id, tag_list, moderated)
            addPost.apply_async(args=[post_id, tag_list, moderated], countdown=12)

            return render(request, 'added-post.html',
                          {'title': title,
                           'cat_list': get_cat_list()})
        else:
            return HttpResponse(str(form.errors))

    form = AddPostForm()

    return render(request, template, {'form': form,
                                             'cat_list': get_cat_list()})


@login_required(redirect_field_name='next', login_url='/login')
@never_cache
def rate_elem(request, type, id, vote):
    """Голосование"""
    if request.method == 'POST':

        user = request.user
        uv = cache.get('user_votes_' + str(user.id))
        votes_amount = user.votes_amount

        if ((uv is None and votes_amount != "B") or
        (uv['votes'] > 0 and votes_amount != "B")):
            date_joined = str(user.date_joined.strftime('%Y_%m_%d'))
            Rate.delay(user.id, date_joined, votes_amount, type, id, vote)
        else:
            return HttpResponse("no votes")

        return HttpResponse("accepted")

@login_required(redirect_field_name='next', login_url='/login')
def complain_elem(request, type, objid, reason):
    if request.method == 'POST' and request.user.can_complain:
        userid = request.user.id
        ComplainObj.delay(type, objid, userid, reason)
        return HttpResponse("Complain accepted")
    else:
        return HttpResponse("Complain not accepted")

#@cache_page(30)
#@cache_control(max_age=30)
#@vary_on_headers('X-Requested-With', 'Cookie')
@never_cache
def list(request, category=None, tag=None, pop=None):
    """
    Лист постов
    Категория/тэг и популярность опциональна
    Пожалуй самая часто используемая вьюшка
    """
    context = {}

    if request.is_ajax():
        template = 'list_ajax.html'
    else:
        template = 'list.html'

    user_known = False
    if request.user.is_authenticated:
        user_known = True
    if not pop:
        pop = 'all'
    page = request.GET.get('page')

    cache_str = "page_" + str(category) + "_" + \
        str(tag) + "_" + str(pop) + "_" + str(user_known) + \
        "_" + str(page)

    if cache.ttl(cache_str):
        posts = cache.get(cache_str)
    else:
        post_list = Post.objects.filter(status="P")
        if tag:
            post_list = post_list.filter(tags__url=tag)
        if category:
            post_list = post_list.filter(category__slug=category)
        if not user_known:
            post_list = post_list.exclude(private=True)
        if pop == "best":
            post_list = post_list.filter(rating__gte=hot_rating)
        post_list = post_list\
                    .prefetch_related("tags", "category", "author", "main_tag")\
                    .only("id", "title", "author", "category", "main_image_srcset",
                     "description", "rating", "created", "url")
                    #.select_related("category", "author")\
                    #.prefetch_related('tags')

        paginator = Paginator(post_list, 3)

        try:
            posts = paginator.page(page).object_list
        except PageNotAnInteger:
            posts = paginator.page(1).object_list
        except EmptyPage:
            posts = None
        cache.set(cache_str, posts, 7200)
    good_posts = get_good_posts(category=category, private=user_known)

    context['good_posts'] = good_posts
    context['posts'] = posts
    context['cat_list'] = get_cat_list()
    context['page'] = page

    if not posts and page:
        return HttpResponse('last_page')
    else:
        return render(request, template, context)


#@cache_page(30)
#@cache_control(max_age=30)
#@vary_on_headers('X-Requested-With', 'Cookie')
@never_cache
def single_post(request, tag, title, id):
    """
    Вьюшка для отдельного поста
    """

    if request.is_ajax():
        template = 'single_ajax.html'
        if not request.user.is_anonymous():
            if request.user.moderator\
            or request.user.is_superuser:
                template = 'single_ajax_moder.html'
    else:
        template = 'single.html'
        if not request.user.is_anonymous():
            if request.user.moderator\
            or request.user.is_superuser:
                template = 'single_moder.html'

    cache_str = "post_single_" + str(id)
    query = Post.objects\
            .prefetch_related("tags", "category", "author", "main_tag")\
            .get(pk=id)
    post = cache.get_or_set(cache_str, query, 7200)

    if post.private and not request.user.is_authenticated:
        return HttpResponseNotFound()

    comment_form = CommentForm()

    comments = Comment.objects.filter(post=post)

    if request.user.is_authenticated:
        user_known = True
    else:
        user_known = False
    good_posts = get_good_posts(category=post.category.id, private=user_known)
    context = {}
    context['good_posts'] = good_posts
    context['post'] = post
    context['cat_list'] = get_cat_list()
    context['comment_form'] = comment_form
    context['comments'] = comments

    return render(request, template, context)


@cache_page(7200)
@cache_control(max_age=7200)
@vary_on_headers('X-Requested-With')
def password_change(request, *args, **kwargs):
    """
    Смена пароля
    """
    if request.is_ajax():
        template = 'registration/password_change_form-ajax.html'
    else:
        template = 'registration/password_change_form.html'

    return def_password_change(request, *args, **kwargs,
                            template_name=template,
                            extra_context={'cat_list': get_cat_list()})
