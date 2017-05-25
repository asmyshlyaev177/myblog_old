import datetime
import json
import os
from django.contrib.auth import views as auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (password_change as def_password_change)
from django.core.cache import cache
from django.db.models import Case, Value, When, Count
from django.http import (HttpResponseRedirect, HttpResponseForbidden, HttpResponse, HttpResponseNotFound)
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.views import generic
from django.views.decorators.cache import cache_control
from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.vary import vary_on_headers
from meta.views import MetadataMixin
from blog.forms import SignupForm, MyUserChangeForm, AddPostForm, CommentForm
from blog.models import (Post, Category, Tag, Comment, MyUser)
from blog.tasks import add_post, rate, comment_image, complain_obj

hot_rating = 3


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
        # start_date = cur_date - delta
        posts = Post.objects \
            .filter(status="P") \
            .filter(rating__gte=0) \
            .order_by("-rating") \
            .prefetch_related("tags", "category", "author", "main_tag") \
            .only("id", "title", "description", "url", "category", "post_image", "author",
                  "main_tag", "main_image_srcset", "private", "rating", "created", "tags",
                  "post_thumb_ext", "post_thumbnail")
        # .filter(published__range=(start_date, cur_date))\
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
        self.user_known = self.request.user.is_authenticated()
        queryset = get_good_posts(category=self.kwargs['category'], private=self.user_known)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(Sidebar, self).get_context_data(**kwargs)
        context['category'] = self.kwargs['category']
        return context


def user_has_rights(user, object):
    result = False
    if not user.is_anonymous:
        cache_str = "user_rights_" + str(type(object)) + "_" + str(object.id)
        if cache.ttl(cache_str):
            result = cache.get(cache_str)
        else:
            if user_is_author(user, object) or \
                    user_is_moder(user, object) or \
                    request.user.is_superuser:
                result = True
            else:
                False
            cache.set(cache_str, result, timeout=900)
    return result


def user_is_moder(user, object):
    result = False
    if type(object) == Post:
        post = object
        post_tags = set(tag for tag in post.tags.values_list('id', flat=True))
        user_moder_tags = \
            set(t for t in user.moderator_of_tags.values_list('id', flat=True))

        if len(post_tags & user_moder_tags) > 0 \
                or post.category.id in user.moderator_of_categories.values_list('id', flat=True):
            result = True
    return result


def user_is_author(user, object):
    if user.id == object.author.id:
        return True
    else:
        return False


def get_cat_list():
    """
    Лист категорий
    """
    if cache.ttl('cat_list'):
        cat_list = cache.get('cat_list')
    else:
        a_day_ago = datetime.date.today() - datetime.timedelta(days=1)
        cat_list = Category.objects.annotate(new=Count(Case(
            When(post__published__gte=a_day_ago, then=Value(1))), default=0, distinct=True)
            # ,pop=Count(Case(
            #  When(post__published__gte=a_day_ago, post__rating__gte=hot_rating,
            # then=Value(1))), default=0, distinct=True)
        )
        cache.set('cat_list', cat_list, 3600)
    return cat_list


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
        query = Comment.objects.filter(post=postid) \
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
            comment_image.delay(comment.id)

            return HttpResponse("OK")


@method_decorator(never_cache, name='dispatch')
class Tags(generic.View):
    def get(self, *args, **kwargs):
        query = Tag.objects.all().values("name")
        tags = cache.get_or_set("taglist", query, 36000)
        data = []
        for tag in tags:
            data.append(tag['name'])
        return HttpResponse(json.dumps(data))


class Signup(generic.edit.FormView):
    template_name = 'registration/signup.html'
    form_class = SignupForm
    success_url = '/signup_success'

    def get_context_data(self, **kwargs):
        context = super(Signup, self).get_context_data(**kwargs)
        context['cat_list'] = get_cat_list()
        context['form'] = SignupForm()
        if self.request.is_ajax():
            self.template_name = 'registration/signup-ajax.html'
        return context

    def post(self, request, *qrgs, **kwargs):
        form = self.get_form()
        if form.is_valid():
            form.save()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class SignupSuccess(generic.View):
    def get(self, *args, **kwargs):
        cat_list = get_cat_list()
        return render(self.request, 'registration/signup_success.html', {'cat_list': cat_list})


@method_decorator([never_cache, login_required], name='dispatch')
class Dashboard(generic.edit.UpdateView):
    template_name = 'dashboard.html'
    form_class = MyUserChangeForm
    success_url = '/dashboard'

    def get_context_data(self, **kwargs):
        context = super(Dashboard, self).get_context_data(**kwargs)
        if self.request.is_ajax():
            self.template_name = 'dashboard-ajax.html'
        context['cat_list'] = get_cat_list()
        return context

    def get_object(self):
        user = MyUser.objects.get(id=self.request.user.id)
        return user


@method_decorator(login_required, name='dispatch')
class MyPosts(generic.ListView):
    template_name = 'dash-my-posts.html'
    allow_empty = True
    context_object_name = 'posts'
    paginate_by = 3
    paginate_orphans = 2
    queryset = Post.objects.all()

    def get_queryset(self):
        posts = self.queryset.filter(author=self.request.user) \
            .prefetch_related("tags", "category", "author", "main_tag").select_related() \
            .only("id", "title", "author", "category", "main_image_srcset", "main_tag", "tags",
                  "description", "rating", "created", "url")
        return posts

    def get_context_data(self, **kwargs):
        context = super(MyPosts, self).get_context_data(**kwargs)
        context['cat_list'] = get_cat_list()
        context['good_posts'] = get_good_posts(private=True)
        if self.request.is_ajax():
            self.template_name = 'dash-my-posts-ajax.html'
        return context


@method_decorator([login_required, never_cache], name='dispatch')
class AddPost(generic.edit.CreateView):
    model = Post
    form_class = AddPostForm
    title = None

    def get_context_data(self, **kwargs):
        if self.request.is_ajax():
            self.template_name = 'add_post-ajax.html'
        else:
            self.template_name = 'add_post.html'
        context = super(AddPost, self).get_context_data(**kwargs)
        context['cat_list'] = get_cat_list()
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.url = slugify(self.object.title, allow_unicode=True)
        tag_list = self.request.POST['hidden_tags'].split(',')
        self.title = self.request.POST['title']
        self.object.save()
        self.success_url = 'post-saved{}'.format(self.object.id)
        group = "post-saved{}".format(self.object.id)
        add_post.apply_async(args=[self.object.id, tag_list, self.request.user.moderated], kwargs={'group': group},
                             countdown=7)
        return super(AddPost, self).form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(AddPost, self).get_form_kwargs()
        # import pdb
        # pdb.set_trace()
        if 'data' in kwargs.keys():
            kwargs['data']._mutable = True
            kwargs['data'].update({'status': 'D'})
            kwargs['data']._mutable = False
        return kwargs

    def render_to_response(self, context, **response_kwargs):
        context['title'] = self.title
        return super(AddPost, self).render_to_response(context, **response_kwargs)


class PostSaved(generic.TemplateView):
    template_name = 'added-post.html'

    def get_context_data(self, **kwargs):
        context = super(PostSaved, self).get_context_data(**kwargs)
        context['cat_list'] = get_cat_list()
        return context


@method_decorator([login_required, never_cache], name='dispatch')
class EditPost(generic.edit.UpdateView):
    model = Post
    form_class = AddPostForm
    context_object_name = 'post'
    title = None

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        tags_list_orig = []
        for tag in self.object.tags.all():
            tags_list_orig.append(tag.name)
        self.tags_list_orig = tags_list_orig

        if user_has_rights(self.request.user, self.object):
            return super(EditPost, self).get(request, *args, **kwargs)
        else:
            return HttpResponseForbidden()

    def post(self, request, *args, **kwargs):
        if user_has_rights(self.request.user, self.get_object()):
            return super(EditPost, self).post(request, *args, **kwargs)
        else:
            return HttpResponseForbidden()

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.url = slugify(self.object.title, allow_unicode=True)
        tag_list_new = self.request.POST['hidden_tags'].split(',')  # tags list
        self.title = self.request.POST['title']
        self.object.save()
        group = "post-saved{}".format(self.object.id)
        self.success_url = 'post-saved{}'.format(self.object.id)
        add_post.apply_async(args=[self.object.id, tag_list_new, self.request.user.moderated], kwargs={'group': group},
                             countdown=7)
        return super(EditPost, self).form_valid(form)

    def get_context_data(self, **kwargs):
        if self.request.is_ajax():
            self.template_name = 'edit_post-ajax.html'
        else:
            self.template_name = 'edit_post.html'
        context = super(EditPost, self).get_context_data(**kwargs)
        context['cat_list'] = get_cat_list()
        context['tags_list'] = self.tags_list_orig
        return context

    def render_to_response(self, context, **response_kwargs):
        context['title'] = self.title
        return super(EditPost, self).render_to_response(context, **response_kwargs)


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
            rate.delay(user.id, date_joined, votes_amount, type, id, vote)
        else:
            return HttpResponse("no votes")

        return HttpResponse("accepted")


@login_required(redirect_field_name='next', login_url='/login')
def complain_elem(request, type, objid, reason):
    if request.method == 'POST' and request.user.can_complain:
        userid = request.user.id
        complain_obj.delay(type, objid, userid, reason)
        return HttpResponse("Complain accepted")
    else:
        return HttpResponse("Complain not accepted")


# @cache_page(30)
# @cache_control(max_age=30)
# @vary_on_headers('X-Requested-With', 'Cookie')
# @never_cache

# @method_decorator(never_cache, name='dispatch')
class List(generic.ListView):
    allow_empty = True
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'list.html'
    queryset = Post.objects.all().filter(status="P")
    paginate_orphans = 2
    user_known = False
    category = None

    def get_context_data(self, **kwargs):
        context = super(List, self).get_context_data(**kwargs)
        self.user_known = self.request.user.is_authenticated
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
        post_list = post_list \
            .prefetch_related("tags", "category", "author", "main_tag", "comment_set") \
            .annotate(comments_count=Count('comment')) \
            .only("id", "title", "author", "category", "main_image_srcset", "main_tag", "tags",
                  "description", "rating", "created", "url")
        return post_list


class ListPop(List):
    def get_queryset(self):
        post_list = super(ListPop, self).get_queryset()
        if self.kwargs['pop'] == "best":
            post_list = post_list.filter(rating__gte=hot_rating)
        return post_list


class ListCat(List):
    def get_queryset(self):
        post_list = super(ListCat, self).get_queryset().filter(category__slug=self.kwargs['category'])
        return post_list


class ListCatPop(ListPop):
    def get_queryset(self):
        post_list = super(ListCatPop, self).get_queryset().filter(category__slug=self.kwargs['category'])
        return post_list


class ListTag(List):
    def get_queryset(self):
        post_list = super(ListTag, self).get_queryset().filter(tags__url=self.kwargs['tag'])
        return post_list


class ListTagPop(ListPop):
    def get_queryset(self):
        post_list = super(ListTagPop, self).get_queryset().filter(tags__url=self.kwargs['tag'])
        return post_list


# @method_decorator(never_cache, name='dispatch')
class SinglePost(generic.DetailView, MetadataMixin):
    context_object_name = 'post'
    user_known = False

    def get_queryset(self):
        cache_str = "post_single_" + str(self.kwargs['pk'])
        query = Post.objects \
            .prefetch_related("tags", "category", "author", "main_tag") \
            .get(pk=self.kwargs['pk'])
        cache.get_or_set(cache_str, query, 7200)
        return Post.objects.filter(id=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super(SinglePost, self).get_context_data(**kwargs)
        comment_form = CommentForm()
        if self.request.is_ajax():
            self.template_name = 'single_ajax.html'
            if user_has_rights(self.request.user, context['post']):
                self.template_name = 'single_ajax_moder.html'
        else:
            self.template_name = 'single.html'
            if user_has_rights(self.request.user, context['post']):
                self.template_name = 'single_moder.html'

        self.user_known = self.request.user.is_authenticated
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
            return super(SinglePost, self).render_to_response(context, **response_kwargs)


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
