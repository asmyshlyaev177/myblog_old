# -*- coding: utf-8 -*-
from django.shortcuts import render
from blog.models import Post, myUser, Category, Tag, Rating, RatingPost,RatingTag,RatingUser,VotePost,UserVotes
from slugify import slugify, SLUG_OK
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
#from unidecode import unidecode
import json
from django.urls import reverse
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.vary import vary_on_headers
from django.views.decorators.cache import cache_control
from django.core.cache import cache

from django.http import (
	HttpResponseBadRequest,
	HttpResponseServerError,
	HttpResponseForbidden,
)
from django.shortcuts import render
#from django_summernote.settings import summernote_config, get_attachment_model
from blog.tasks import addPost, RatePost

cat_list= Category.objects.all()

@never_cache
def tags(request):
	tags = Tag.objects.all().values().cache()
	data = []
	for i in tags:
		data.append(i['name'])

	return HttpResponse(json.dumps(data), content_type="application/json")


@csrf_protect
@never_cache
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
@cache_page( 10 )
@vary_on_headers('X-Requested-With','Cookie')
@cache_control(max_age=10,private=True)
#@never_cache
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
@cache_page(30 )
@cache_control(max_age=30, private=True)
@vary_on_headers('X-Requested-With','Cookie')
#@never_cache
def my_posts(request):
	if request.is_ajax() == True :
		template = 'dash-my-posts-ajax.html'
	else:
		template = 'dash-my-posts.html'
	post_list = Post.objects.filter(author=request.user.id).cache()

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
			if request.user.moderated:
				moderated = True
			else:
				moderated = False

			data.author = request.user
			data.url = slugify(data.title)
			title = data.title
			tag_list = request.POST['hidden_tags'].split(',') # tags list

			have_new_tags = False
			data.save()
			post_id = data.id
			addPost.delay(post_id, tag_list, moderated)



			return render(request, 'added-post.html',
						  {'title': title,
						   'cat_list':cat_list})


	form = AddPostForm()

	return render(request, template, { 'form': form,
											 'cat_list': cat_list})

@login_required(redirect_field_name='next', login_url='/login')
@never_cache
def rate_post(request, postid, vote):
	if request.method == 'POST':

		user = request.user
		if user.has_votes:
			RatePost.delay(user.id, postid, vote)
		else:
			return HttpResponse("no votes")

		return HttpResponse("accepted")

@cache_page(60 )
@cache_control(max_age=60)
@vary_on_headers('X-Requested-With','Cookie')
#@never_cache
def list(request, category=None, tag=None, pop=None):

	context = {}

	if request.is_ajax() == True :
		template = 'list_ajax.html'
	else:
		template = 'list.html'

	if tag:
		post_list= Post.objects.select_related("author", "category")\
			.prefetch_related('tags').filter(tags__url=tag)\
			.filter(status="P").cache()#.order_by('-published')
		#context['tag'] = Tag.objects.get(url=tag)
		if category:
			post_list = post_list.filter(category__slug=category).cache()
			context['category'] = category

	else:
		if category:
			post_list= Post.objects.select_related("author", "category")\
				.prefetch_related('tags').filter(category__slug=category)\
				.filter(status="P").cache()
		else:
			post_list = Post.objects.select_related("author", "category")\
				.prefetch_related('tags').filter(status="P").cache()#.order_by('-published')

	if not request.user.is_authenticated:
		post_list = post_list.filter(private=False).cache()
	#if pop:
	#	pass filter

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

@cache_page(180)
@cache_control(max_age=180)
@vary_on_headers('X-Requested-With', 'Cookie')
#@never_cache
def single_post(request,  tag, title, id):

	if request.is_ajax() == True :
		template = 'single_ajax.html'
	else:
		template = 'single.html'

	post = Post.objects.select_related("author", "category")\
		.prefetch_related('tags').cache().get(pk=id)

	if post.private == True and not request.user.is_authenticated:
		return HttpResponseNotFound()

	return render(request, template,
				  {'post': post,
				  'cat_list': Category.list()})


@sensitive_post_parameters()
@csrf_protect
@login_required(redirect_field_name='next', login_url='/login')
@deprecate_current_app
#@cache_page(2)
#@cache_control(max_age=2, private=True)
#@vary_on_headers('X-Requested-With','Cookie')
@never_cache
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
