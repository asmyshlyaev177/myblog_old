# -*- coding: utf-8 -*-
from celery import Celery
from celery.task import periodic_task
from datetime import timedelta
import os, datetime, json, re
from blog.models import (Post, RatingPost,RatingTag, Tag, Rating, myUser,
						UserVotes, RatingUser, VotePost)
from slugify import slugify, SLUG_OK
from bs4 import BeautifulSoup
from PIL import Image
from urllib.parse import urlparse, urlencode
import datetime
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
def RatePost(userid, postid, vote):
	post = Post.objects.get(id=postid)
	user = myUser.objects.get(id=userid)
	delta = datetime.timedelta(weeks=4)
	dt = datetime.datetime.now(tz=tz)

	uv = cache.get('user_votes_' + str(user.id))

	if uv == None and user.votes_count != "B":
		votes = {}
		if user.date_joined < dt - delta:
			coef = 0.25
			if user.votes_count == "N":
				votes['votes'] = 20
		else:
			coef = 0.0
			if user.votes_count == "N":
				votes['votes'] = 10

		votes['weight'] = 0.25 + coef # + user_rating.rating/50
		print("REDIS User: " + str(user)+" weight "+str(votes['weight'])\
			+ " votes "+ str(votes['votes']))

		cache.set('user_votes_' + str(userid), votes, timeout=600) #86400 -1 day
		uv = cache.get('user_votes_' + str(user.id))

	uv_ttl = cache.ttl('user_votes_' + str(userid))


	if post.rateable and uv['votes'] > 0 and user.votes_count != "B" :
		# example   vote_post_248_2016_12_17_20:14:49:915851
		today = datetime.datetime.today().strftime('%Y_%m_%d_%H:%M:%S:%f')
		r_key = 'vote_post_' + str(postid)+'_' + today
		if vote == str(1):
			score = uv['weight']
		else:
			score = -uv['weight']
		if user.votes_count == "N":
			uv['votes'] -= 1
		cache.set(r_key, score, timeout=3024000)
		cache.set('user_votes_' + str(userid), uv, timeout=uv_ttl)


@app.task(name="CalcPostRating")
def CalcPostRating():
	#another task

	dt = datetime.datetime.now(tz=tz)#.replace(second=0, microsecond=0)
	rt = datetime.timedelta(hours=-1)
	day = datetime.timedelta(hours=-24)
	week = datetime.timedelta(days=-7)
	month = datetime.timedelta(weeks=-4)
	two_month = datetime.timedelta(weeks=-8)
	end = dt

	#vote_list = VotePost.objects.all().cache()
	#v = vote_list.values_list('post', flat=True).distinct().cache()
	vote_list = VotePost.objects.all()
	v = vote_list.values_list('post', flat=True).distinct()
	post_ids = set()
	for i in v:
		post_ids.add(i)

	#posts = Post.objects.filter(id__in=post_ids).filter(status="P").filter(rateable = True).cache()
	#ratings = RatingPost.objects.filter(post__id__in=post_ids).cache()
	posts = Post.objects.filter(id__in=post_ids).filter(status="P").filter(rateable = True)
	ratings = RatingPost.objects.filter(post__id__in=post_ids)

	for post in posts:
		rt_change = False
		day_change = False
		week_change = False
		month_change = False

		post_rating, notexist = ratings.get_or_create(post=post)
		tag_rating, notexist = RatingTag.objects.get_or_create(tag=post.main_tag)
		author_rating, notexist = RatingUser.objects.get_or_create(user=post.author)

		#rating
		sum = 0.0
		votes_count = 0
		start = dt + rt
		votes = vote_list.filter(post=post).filter(counted=False)\
			.filter(created__range=(start, end))
		if votes.count() > 0:
			print("******")
			print("Counting votes")
			print("******")

			for i in votes:
				if i.rate == 0:
					sum -= i.score
				if i.rate == 1:
					sum += i.score
				#votes_count += 1
				i.counted = True
				i.save()
			#post_rating.votes += votes_count
			post_rating.rating += sum
			#tag_rating.votes += votes_count
			tag_rating.rating += sum/50
			author_rating.rating += sum/50
			#author_rating.votes += votes_count
			author_rating.save()
			rt_change = True

		if rt_change:
			print("save rating for post - ", str(post))
			post_rating.save()
			tag_rating.save()

		"""#rating for day
		sum = 0.0
		start = dt.replace(second=0, microsecond=0, minute=0) + day
		votes = vote_list.filter(post=post).filter(created__range=(start, end))
		for i in votes:
			if i.rate == 0:
				sum -= i.score
			if i.rate == 1:
				sum += i.score

		if post_rating.day != sum:
			print("Counting votes for day")
			post_rating.day = sum
			tag_rating.day = sum/50
			day_change = True


		#rating for last week
		sum = 0.0
		start = dt.replace(second=0, microsecond=0, minute=0, hour=0) + week
		votes = vote_list.filter(post=post).filter(created__range=(start, end))
		for i in votes:
			if i.rate == 0:
				sum -= i.score
			if i.rate == 1:
				sum += i.score

		if post_rating.week != sum:
			post_rating.week = sum
			tag_rating.week = sum/50
			week_change = True

		#rating for last month
		sum = 0.0
		start = dt.replace(second=0, microsecond=0, minute=0, hour=0, day=1) + month
		votes = vote_list.filter(post=post).filter(created__range=(start, end))
		for i in votes:
			if i.rate == 0:
				sum -= i.score
			if i.rate == 1:
				sum += i.score

		if post_rating.month != sum:
			print("Counting votes for month")
			post_rating.month = sum
			tag_rating.month = sum/50
			month_change = True

		if rt_change or day_change or week_change or month_change:
			print("save rating for post - ", str(post))
			post_rating.save()
			tag_rating.save() """

@app.task(name="deleteOldVotes")
def deleteOldVotes():
	delta_tz = datetime.timedelta(hours=+3)
	tz = datetime.timezone(delta_tz)
	dt = datetime.datetime.now(tz=tz)

	dt = datetime.datetime.now()
	start = dt + datetime.timedelta(weeks=-96)
	end = dt + datetime.timedelta(weeks=-4, days=-3)
	VotePost.objects.all().filter(created__range=(start, end)).delete()

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
