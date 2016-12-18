# -*- coding: utf-8 -*-
from celery import Celery
from celery.task import periodic_task
from datetime import timedelta
import os, datetime, json, re
from blog.models import (Post, RatingPost,RatingTag, Tag, Rating, myUser,
						UserVotes, RatingUser, VotePost, Category)
from slugify import slugify, SLUG_OK
from bs4 import BeautifulSoup
from PIL import Image
from urllib.parse import urlparse, urlencode
import datetime, pickle, pytz
#from django.utils import timezone
#from django.http import (HttpResponse,JsonResponse)
from urllib.request import urlopen, urlretrieve, Request
from django.utils.encoding import uri_to_iri, iri_to_uri
from blog.functions import srcsets, findFile, findLink, srcsetThumb
from time import gmtime, strftime
from django.core.cache import cache

app = Celery('tasks', broker='pyamqp://guest@localhost//')


#@periodic_task(run_every=timedelta(seconds=10))
"""@app.task(name='taglist')
def taglist():
	tags = Tag.objects.all().values()
	data = []
	for i in tags:
		data.append(i['name'])
	filename = "/root/myblog/myblog/blog/static/taglist.json"
	with open(filename, 'w', encoding='utf8') as out:
		out.write(json.dumps(data), ensure_ascii=False)
		"""

delta_tz = datetime.timedelta(hours=+3)
tz = datetime.timezone(delta_tz)

@app.task(name="RatePost")
def RatePost(userid, date_joined, votes_count, postid, vote):
	post = Post.objects.get(id=postid)
	#user = myUser.objects.get(id=userid)
	delta = datetime.timedelta(weeks=4)
	dt = datetime.datetime.now(tz=tz)
	uv = cache.get('user_votes_' + str(userid))

	if uv == None:  #user votes кол-во голосов у юзеров
		date_joined = pytz.utc.localize\
			(datetime.datetime.strptime(date_joined, '%Y_%m_%d'))

		votes = {}
		if date_joined < dt - delta:
			coef = 0.25
			votes['votes'] = 20
		else:
			coef = 0.0
			votes['votes'] = 10

		votes['weight'] = 0.25 + coef # + user_rating.rating/50
		print("REDIS User: " + str(userid)+" weight "+str(votes['weight'])\
			+ " votes "+ str(votes['votes']))

		cache.set('user_votes_' + str(userid), votes, timeout=150) #86400 -1 day

		uv = cache.get('user_votes_' + str(userid))

	uv_ttl = cache.ttl('user_votes_' + str(userid))

	if post.rateable:
		if uv['votes'] > 0 :
			p_data = {}

			# example   vote_post_2016_12_17_20_14_49_915851
			today = datetime.datetime.today().strftime('%Y_%m_%d_%H_%M_%S_%f')
			r_key = 'vote_post_' + today
			if vote == str(1):
				p_data['rate'] = uv['weight']
			else:
				p_data['rate'] = -uv['weight']
			if votes_count == "N":
				uv['votes'] -= 1
			p_data['category'] = post.category.id
			p_data['postid'] = post.id

			cache.set(r_key, p_data, timeout=3024000)
			#уменьшаем кол-во голосов у пользователя
			cache.set('user_votes_' + str(userid), uv, timeout=uv_ttl)


@app.task(name="CalcPostRating")
def CalcPostRating():
	hot_rating = 1.0
	cat_list = Category.objects.all()

	votes = cache.iter_keys('vote_post_*')
	posts = {}
	for i in votes:
		vote = cache.get(i)
		cache.delete(i)
		if not vote['postid'] in posts:
			posts[ vote['postid'] ] = {}
			posts[ vote['postid'] ]['category'] = vote['category']
			posts[ vote['postid'] ]['rate'] = vote['rate']
			posts[ vote['postid'] ]['id'] = vote['postid']
		else:
			posts[ vote['postid'] ]['rate'] += vote['rate']
	today = datetime.datetime.today().strftime('%H')
	cache.set('rating_post_day_'+today, posts, timeout=88000)
	del votes
	for post in posts: #update rating on posts
		post_rate, _ = RatingPost.objects.get_or_create(post=post)
		post_rate.rating += posts[post]['rate']
		post_rate.save()

	#rating for main page
	best_posts = {}
	keys = cache.keys('rating_post_day_*')
	for k in keys:
		posts = cache.get(k)
		posts = [ posts[post] for post in posts]
		for post in posts:
			if not post['id'] in best_posts:
				best_posts[ post['id'] ] = post['rate']
			else:
				best_posts[ post['id'] ] += post['rate']
		#filtr by rating
	best_posts = [ post for post in best_posts if best_posts[post] > hot_rating ]
	cache.set('best_post_day_all', best_posts, timeout=88000)


	for i in cat_list: #make ratings for categories
		best_posts = {}
		keys = cache.keys('rating_post_day_*')
		for k in keys:
			posts = cache.get(k)
			posts = [ posts[post] for post in posts if posts[post]['category'] == i.id ]
			for post in posts:
				if not post['id'] in best_posts:
					best_posts[ post['id'] ] = post['rate']
				else:
					best_posts[ post['id'] ] += post['rate']
			#filtr by rating
		best_posts = [ post for post in best_posts if best_posts[post] > hot_rating ]
		cache.set('best_post_day_catid_' + str(i.id), best_posts, timeout=88000)


@app.task(name="addPost")
def addPost(post_id, tag_list, moderated):
	data = Post.objects.get(id=post_id)
	j = True
	nsfw = data.private
	have_new_tags = False
	for i in tag_list:
		if len(i) > 2:
			if nsfw == True:
				tag_url = slugify(i.lower()+"_nsfw")
				try:
					tag = Tag.objects.get(url__iexact=tag_url)
				except:
					have_new_tags = True
					tag = Tag.objects.create(name=i, url=tag_url)
			else:
				tag_url = slugify(i.lower())
				try:
					tag = Tag.objects.get(url__iexact=tag_url)
				except:
					have_new_tags = True
					tag = Tag.objects.create(name=i, url=tag_url)

			if have_new_tags:
				tag.save()
			data.tags.add(tag)
		if j:
			try:
				data.main_tag = tag
			except:
				#tag = Tag.objects.cache().get(id=8)
				tag = Tag.objects.get(id=8)
				data.main_tag = tag
			j = False


		# создаём картинки из текста
		soup = srcsets(data.text, True)
		# выравниваем видео по центру
		ifr_links = soup.find_all("iframe")
		ifr_class = []
		if len(ifr_links) != 0:
			for i in ifr_links:
				for j in i['class']:
					ifr_class.append(j)
				ifr_class = [item for item in ifr_class if not item.startswith('center-align')]
				ifr_class.append('center-align')
				i['class'] = ifr_class

		soup.html.unwrap()
		#soup.head.unwrap()
		soup.body.unwrap()
		data.text = soup.prettify()

		#image from url

		if data.image_url:
			today = datetime.date.today()
			upload_path1 = '/root/myblog/myblog/blog/static/media/' + \
			str(today.year)+'/' +str(today.month)+'/'+str(today.day)+'/'
			upload_path = str(today.year)+'/' +str(today.month)+'/'+str(today.day)+'/'
			filename = urlparse(data.image_url).path.split('/')[-1]
			save_path = os.path.join(upload_path1, filename)
			user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
			headers = { 'User-Agent' : user_agent }
			values = {'name' : 'Alex',
		  				'location' : 'Moscow',}
			data2 = urlencode(values)
			data2 = data2.encode('ascii')

			try:
				req = Request(data.image_url, data2, headers, method="GET")
				os.makedirs(os.path.dirname(upload_path), exist_ok=True)
				with urlopen(req, timeout=7) as response, open(save_path, 'wb') as out_file:
					data2 = response.read()
					out_file.write(data2)
				data.post_image = os.path.join(upload_path, filename)
			except:
				pass
			data.image_url = ""

		if data.post_image and data.post_image_gif() == False:
			data.image_url = srcsetThumb(data.post_image)

		if not moderated:
			data.status = "P"
		data.save()
		cache.delete_pattern("post_list_*")
		#tag_rating, _ = RatingTag.objects.cache().get_or_create(tag=tag)
		tag_rating, _ = RatingTag.objects.get_or_create(tag=tag)
		tag_rating.tag = tag
		tag_rating.rating = 0
		tag_rating.save()
		#post_rating, _ = RatingPost.objects.cache().get_or_create(post=data)
		post_rating, _ = RatingPost.objects.get_or_create(post=data)
		post_rating.post = data
		if _:
			post_rating.rating = 0.0
		post_rating.save()
		"""try:
			if have_new_tags:
				pass
				#taglist.delay()
		except:
			pass"""
