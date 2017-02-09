# -*- coding: utf-8 -*-
from celery import Celery
from datetime import timedelta
import os, datetime, json, re
from blog.models import (Post, RatingPost, RatingTag, RatingComment, Tag,
                        RatingUser, Category, Comment)
##from slugify import slugify, SLUG_OK
from django.utils.text import slugify
from bs4 import BeautifulSoup
from PIL import Image
from urllib.parse import urlparse, urlencode
import datetime, pytz
# from django.utils import timezone
# from django.http import (HttpResponse,JsonResponse)
from urllib.request import urlopen, Request
from blog.functions import srcsets, srcsetThumb
from django.core.cache import cache
from channels import Group
from myblog.celery import app

#app = Celery('myblog', broker='amqp://django:Qvjuzowu177Qvjuzowu177Qvjuzowu177@rabbitmq:5672//')

delta_tz = datetime.timedelta(hours=+3)
tz = datetime.timezone(delta_tz)


@app.task(name="Rate")
def Rate(userid, date_joined, votes_count, type, elem_id, vote):

    if type == "post":
        element = Post.objects.get(id=elem_id)
    elif type == "comment":
        element = Comment.objects.get(id=elem_id)

    # user = myUser.objects.get(id=userid)
    delta = datetime.timedelta(weeks=4)
    dt = datetime.datetime.now(tz=tz)
    uv = cache.get('user_votes_' + str(userid))

    if uv is None:   # user votes кол-во голосов у юзеров
        date_joined = pytz.utc.localize\
            (datetime.datetime.strptime(date_joined, '%Y_%m_%d'))
        user_rating = RatingUser.objects.get(user=userid)
        votes = {}
        if date_joined < dt - delta:
            coef = 0.25
            votes['votes'] = 200
        else:
            coef = 0.0
            votes['votes'] = 100

        votes['weight'] = 0.25 + coef + user_rating.rating / 50
        print("REDIS User: " + str(userid) + " weight " + str(votes['weight']) +
                                                " votes " + str(votes['votes']))

        cache.set('user_votes_' + str(userid), votes, timeout=150)  # 86400 -1 day

        uv = cache.get('user_votes_' + str(userid))

    uv_ttl = cache.ttl('user_votes_' + str(userid))

    if uv['votes'] > 0:
        p_data = {}
        today = datetime.datetime.today().strftime('%Y_%m_%d_%H_%M_%S_%f')
        if vote == str(1):
            p_data['rate'] = uv['weight']
        else:
            p_data['rate'] = -uv['weight']
        p_data['elem_id'] = element.id
        if votes_count == "N":
            # уменьшаем кол-во голосов у пользователя
            uv['votes'] -= 1
        r_key = 'vote_' + type + '_' + today

        if type == "post":
            if element.rateable:
                # example   vote_post_2016_12_17_20_14_49_915851
                p_data['category'] = element.category.id
                cache.set(r_key, p_data, timeout=3024000)
        elif type == "comment":
                # example vote_comment_2016_12_24_23_16_35_968626
                # {'elem_id': 55, 'rate': -0.5}
            cache.set(r_key, p_data, timeout=3024000)

        cache.set('user_votes_' + str(userid), uv, timeout=uv_ttl)


@app.task(name="CalcRating")
def CalcRating():
    # hot_rating = 1.0
    # cat_list = Category.objects.all()
    # today = datetime.datetime.today().strftime('%H')

    # рэйтинг для комментов
    votes_comment = cache.iter_keys('vote_comment_*')
    comments = {}
    for i in votes_comment:
        vote = cache.get(i)
        cache.delete(i)
        if not vote['elem_id'] in comments:
            comments[vote['elem_id']] = {}
            comments[vote['elem_id']]['rate'] = vote['rate']
            comments[vote['elem_id']]['id'] = vote['elem_id']
        else:
            comments[vote['elem_id']]['rate'] += vote['rate']
    del votes_comment
    for comment in comments:  # update rating on comments
        com = Comment.objects.get(id=comment)
        comment_rate, _ = RatingComment.objects.get_or_create(comment=com)
        comment_rate.rating += comments[comment]['rate']
        comment_rate.save()

    votes_post = cache.iter_keys('vote_post_*')
    posts = {}
    for i in votes_post:
        vote = cache.get(i)
        cache.delete(i)
        if not vote['elem_id'] in posts:
            posts[vote['elem_id']] = {}
            posts[vote['elem_id']]['category'] = vote['category']
            posts[vote['elem_id']]['rate'] = vote['rate']
            posts[vote['elem_id']]['id'] = vote['elem_id']
        else:
            posts[vote['elem_id']]['rate'] += vote['rate']

    # cache.set('rating_post_day_' + today, posts, timeout=88000)
    del votes_post
    for post in posts:  # update rating on posts
        p = Post.objects.get(id=post)
        post_rate, _ = RatingPost.objects.get_or_create(post=p)
        user_rating = RatingUser.objects.get(user=p.author.id)
        post_rate.rating += posts[post]['rate']
        user_rating.rating += posts[post]['rate'] / 30
        post_rate.save()
        user_rating.save()

    """    # rating for main page
    best_posts = {}   # доделать рейтинги за неделю, не за день
    keys = cache.keys('rating_post_day_*')
    for k in keys:
        posts = cache.get(k)
        posts = [posts[post] for post in posts]
        for post in posts:
            if not post['id'] in best_posts:
                best_posts[post['id']] = post['rate']
            else:
                best_posts[post['id']] += post['rate']
        # filtr by rating
    best_posts = [post for post in best_posts if best_posts[post] > hot_rating]
    cache.set('best_post_day_all', best_posts, timeout=88000)

    for i in cat_list:  # make ratings for categories
        best_posts = {}
        keys = cache.keys('rating_post_day_*')
        for k in keys:
            posts = cache.get(k)
            posts = [posts[post] for post in posts if posts[post]['category'] == i.id]
            for post in posts:
                if not post['id'] in best_posts:
                    best_posts[post['id']] = post['rate']
                else:
                    best_posts[post['id']] += post['rate']
            # filtr by rating
        best_posts = [post for post in best_posts if best_posts[post] > hot_rating]
        cache.set('best_post_day_catid_' + str(i.id), best_posts, timeout=88000)
        """


@app.task(name="commentImage")
def commentImage(comment_id):
    data = Comment.objects.get(id=comment_id)

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
    # soup.head.unwrap()
    soup.body.unwrap()
    data.text = soup.prettify()
    data.save()

    cache_str = "comment_" + str(data.post.id)
    cache.delete(cache_str)

    c = {}
    c['id'] = data.id
    if data.parent:
        c['parent'] = data.parent.id
    c['author'] = data.author.username
    if data.author.avatar:
        c['avatar'] = data.author.avatar.url
    else:
        c['avatar'] = "/media/avatars/admin/avatar.jpg"

    if data.level != 0:
        c['parent'] = data.parent.id
    else:
        c['parent'] = 0
    c['text'] = data.text
    c['level'] = data.level
    c['comment'] = 1
    c['created'] = (data.created + delta_tz).strftime('%Y.%m.%d %H:%M')
    group = data.post.get_absolute_url().strip('/').split('/')[-1]
    Group(group).send({
        # "text": "[user] %s" % message.content['text'],
        "text": json.dumps(c),
                        })


@app.task(name="addPost")
def addPost(post_id, tag_list, moderated):
    data = Post.objects.get(id=post_id)
    j = True
    nsfw = data.private
    have_new_tags = False
    for i in tag_list:
        if len(i) > 2:
            if nsfw:
                tag_url = slugify(i.lower() + "_nsfw", allow_unicode=True)
                try:
                    tag = Tag.objects.get(url__iexact=tag_url)
                except:
                    have_new_tags = True
                    tag = Tag.objects.create(name=i, url=tag_url)
            else:
                tag_url = slugify(i.lower(), allow_unicode=True)
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
                #tag = Tag.objects.get(id=8)
                tag, _ = Tag.objects.get_or_create(name="Разное")
                if _:
                    tag.url = "others"
                    tag.save()
                data.main_tag = tag
            j = False

    # ищем картинки в тексте
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
    soup.head.unwrap()
    soup.body.unwrap()
    data.text = soup.prettify()

    # image from url

    if data.image_url:
        today = datetime.date.today()
        upload_path1 = '/root/myblog/myblog/blog/static/media/' + \
        str(today.year) + '/' + str(today.month) + '/' + str(today.day) + '/'
        upload_path = str(today.year) + '/' + str(today.month) + \
                                        '/' + str(today.day) + '/'
        filename = urlparse(data.image_url).path.split('/')[-1]
        save_path = os.path.join(upload_path1, filename)
        user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
        headers = {'User-Agent': user_agent}
        values = {'name': 'Alex',
                      'location': 'Moscow', }
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

    if data.post_image and not data.post_image_gif():
        data.main_image_srcset = srcsetThumb(data.post_image)
        # data.image_url = srcsetThumb(data.post_image)

    if not moderated:
        data.status = "P"
    data.save()
    cache.delete_pattern("post_list_*")
    cache_str = "post_single_" + str(data.id)
    cache.delete(cache_str)
    # tag_rating, _ = RatingTag.objects.cache().get_or_create(tag=tag)
    tag_rating, _ = RatingTag.objects.get_or_create(tag=tag)
    tag_rating.tag = tag
    tag_rating.rating = 0
    tag_rating.save()
    # post_rating, _ = RatingPost.objects.cache().get_or_create(post=data)
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
