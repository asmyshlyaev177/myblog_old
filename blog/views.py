# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.utils.text import slugify
from django.http import (HttpResponseRedirect, HttpResponseForbidden,
                        HttpResponse, HttpResponseNotFound, Http404)
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, InvalidPage
import json, sys, os, datetime
from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.vary import vary_on_headers
from django.views.decorators.cache import cache_control
from django.core.cache import cache
from django.views import generic
from meta.views import MetadataMixin
from django.utils.decorators import method_decorator
from blog.tasks import addPost, Rate, commentImage, ComplainObj
from django.contrib.auth.views import (login as def_login,
                                password_change as def_password_change)

from blog.forms import SignupForm, MyUserChangeForm, AddPostForm, CommentForm
from blog.models import (Post, Category, Tag, Comment, myUser, Complain)
hot_rating = 3

import resource

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
                .only("id", "title", "description", "url", "category", "post_image", "author",
                    "main_tag", "main_image_srcset", "private", "rating", "created", "tags",
                     "post_thumb_ext", "post_thumbnail")
                #.filter(published__range=(start_date, cur_date))\
        if category:
            posts = posts.filter(category__slug=category)
        if not private:
            posts = posts.exclude(private=True)
        posts = list(posts[0:4])
        cache.set(cache_str, posts, 7200)
    return posts





class Sidebar(generic.ListView):
    context_object_name = 'good_posts'
    template_name = "sidebar.html"
    
    def get_queryset(self, **kwargs):
        self.user_known = user_is_auth(self.request)
        queryset = get_good_posts(category=self.kwargs['category'], private=self.user_known)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super(Sidebar, self).get_context_data(**kwargs)
        context['category'] = self.kwargs['category']
        return context
    

def user_is_auth(request):
    if request.user.is_authenticated:
            return True
    else:
            return False

def user_is_moder(request):
    if not request.user.is_anonymous():
        if request.user.moderator\
        or request.user.is_superuser:
            return True
        else:
            return False
    else:
        return False

def get_cat_list():
    """
    Лист категорий
    """
    return cache.get_or_set("cat_list", Category.objects.all(), 36000)


@method_decorator(never_cache, name='dispatch')
class Login(auth.LoginView):
    """
    Логин
    """
    def get_context_data(self, **kwargs):
        context = super(Login, self).get_context_data(**kwargs)
        if self.request.is_ajax():
            self.template_name = 'registration/login_ajax.html'
        else:
            self.template_name = 'registration/login.html'
        context['cat_list'] = get_cat_list()
        return context


def get_comments(postid):
    cache_str = "comment_" + str(postid)
    if cache.ttl(cache_str):
        comments = cache.get(cache_str)
    else:    
        query = Comment.objects.filter(post=postid)\
            .prefetch_related("author")
        comments = cache.set(cache_str, query, 3600)
    return comments
        
class Comments(generic.TemplateView):
    template_name = 'comments-ajax.html'
    
    def get_context_data(self, **kwargs):
        context = super(Comments, self).get_context_data(**kwargs)
        context['comments'] = get_comments(self.kwargs['postid'])
        return context
    

@method_decorator([login_required, never_cache], name='dispatch')
class AddComment(generic.View):
    http_method_names = [u'post']
    parent = 0
    
    def post(self, request, *args, **kwargs):
        form = CommentForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                self.parent = int(self.kwargs['parent'])
            except:
                pass
            comment = form.save(commit=False)
            comment.author = self.request.user
            comment.post = Post.objects.only('id').get(id=self.kwargs['postid'])
            if self.parent != 0:
                comment.parent = Comment.objects.only('id').get(id=self.parent)
            comment.save()
            commentImage.delay(comment.id)

            return HttpResponse("OK")


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
        if not request.POST._mutable:
            request.POST._mutable = True
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
#@never_cache

#@method_decorator(never_cache, name='dispatch')
class List(generic.ListView):
    allow_empty = True
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'list.html'
    queryset = Post.objects.filter(status="P")
    paginate_orphans = 2
    user_known = False
    category = None
    tag = None
    pop = None
    page = None
    
    def get_context_data(self, **kwargs):
        context = super(List, self).get_context_data(**kwargs)
        self.user_known = user_is_auth(self.request)
        try:
            self.category = self.kwargs['category']
        except:
            pass
        
        context['good_posts'] = get_good_posts(category=self.category,
                                               private=self.user_known)
        context['cat_list'] = get_cat_list()
        if self.request.is_ajax():
            self.template_name = 'list_ajax.html'
            
        return context
    
    def get_queryset(self):
        post_list = self.queryset
        if not self.user_known:
            post_list = post_list.exclude(private=True)
        post_list = post_list\
                    .prefetch_related("tags", "category", "author", "main_tag")\
                    .only("id", "title", "author", "category", "main_image_srcset", "main_tag", "tags",
                     "description", "rating", "created", "url")
        return post_list
        

    
    
class List_pop(List):
    def get_queryset(self):
        post_list = super(List_pop, self).get_queryset()
        if self.kwargs['pop'] == "best":
            post_list = post_list.filter(rating__gte=hot_rating)
        return post_list
    
class List_cat(List):
    def get_queryset(self):
        post_list = super(List_cat, self).get_queryset().filter(category__slug=self.kwargs['category'])
        return post_list
    
class List_cat_pop(List_pop):
    def get_queryset(self):
        post_list = super(List_cat_pop, self).get_queryset().filter(category__slug=self.kwargs['category'])
        return post_list
    
class List_tag(List):
    def get_queryset(self):
        post_list = super(List_tag, self).get_queryset().filter(tags__url=self.kwargs['tag'])
        return post_list
    
class List_tag_pop(List_pop):
    def get_queryset(self):
        post_list = super(List_tag_pop, self).get_queryset().filter(tags__url=self.kwargs['tag'])
        return post_list
    
    

#@method_decorator(never_cache, name='dispatch')
class Single_post(generic.DetailView, MetadataMixin):
    context_object_name = 'post'
    user_known = False
    
    def get_queryset(self):
        cache_str = "post_single_" + str(self.kwargs['pk'])
        query = Post.objects\
                .prefetch_related("tags", "category", "author", "main_tag")\
                .get(pk=self.kwargs['pk'])
        cache.get_or_set(cache_str, query, 7200)
        return Post.objects.filter(id=self.kwargs['pk'])
    
    def get_context_data(self, **kwargs):
        context = super(Single_post, self).get_context_data(**kwargs)
        comment_form = CommentForm()
        if self.request.is_ajax():
            self.template_name = 'single_ajax.html'
            if user_is_moder(self.request):
                self.template_name = 'single_ajax_moder.html'
        else:
            self.template_name = 'single.html'
            if user_is_moder(self.request):
                self.template_name = 'single_moder.html'
                    
        self.user_known = user_is_auth(self.request)
        context['good_posts'] = get_good_posts(category=self.get_queryset()[0].category.id,
                                               private=self.user_known)
        context['cat_list'] = get_cat_list()
        context['meta'] = self.get_object().as_meta(self.request)
        context['comment_form'] = comment_form
        context['comments'] = get_comments(self.kwargs['pk'])
        return context

    def render_to_response(self, context, **response_kwargs):
        if context['post'].private and not self.request.user.is_authenticated:
            return HttpResponseNotFound()
        else:
            return super(Single_post, self).render_to_response(context, **response_kwargs)


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
