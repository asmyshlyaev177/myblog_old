# -*- coding: utf-8 -*-
from celery import Celery
from datetime import timedelta
import os, datetime, json, re
from blog.models import (myUser, Post, Tag, Category, Comment)
from django.utils.text import slugify
from bs4 import BeautifulSoup
from PIL import Image
from urllib.parse import urlparse, urlencode
import datetime, pytz
from urllib.request import urlopen, Request
from blog.functions import (srcsets, srcsetThumb,
                            sidebarThumbnail, stripMediaFromPath)
from django.core.cache import cache
from channels import Group
from myblog.celery import app

#app = Celery('myblog', broker='amqp://django:Qvjuzowu177Qvjuzowu177Qvjuzowu177@rabbitmq:5672//')

delta_tz = datetime.timedelta(hours=+3)
tz = datetime.timezone(delta_tz)


@app.task(name="Rate")
def Rate(userid, date_joined, votes_count, type, elem_id, vote):

    if type == "post":
        element = Post.objects.only('id', 'rateable', 'category')\
            .select_related('category').get(id=elem_id)
    elif type == "comment":
        element = Comment.objects.only('id').get(id=elem_id)

    delta = datetime.timedelta(weeks=4)
    dt = datetime.datetime.now(tz=tz)
    uv = cache.get('user_votes_' + str(userid))

    if uv is None:   # user votes кол-во голосов у юзеров
        date_joined = pytz.utc.localize\
            (datetime.datetime.strptime(date_joined, '%Y_%m_%d'))
        user_rating = myUser.objects.only('rating').get(id=userid)
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
        uv = votes

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

        return "Element type {} with id {} rated".format(str(type), str(elem_id))
    else:
        return "No votes for user with id {},\
            type {} with id {} rated"\
            .format(str(user_id), str(type), str(elem_id))


@app.task(name="CalcRating")
def CalcRating():
    # hot_rating = 1.0
    # cat_list = Category.objects.all()
    # today = datetime.datetime.today().strftime('%H')

    # рэйтинг для комментов
    votes_comment = cache.iter_keys('vote_comment_*')
    comments_rates = {}
    for i in votes_comment:
        vote = cache.get(i)
        cache.delete(i)
        if not vote['elem_id'] in comments_rates:
            comments_rates[vote['elem_id']] = {}
            comments_rates[vote['elem_id']]['rate'] = vote['rate']
            comments_rates[vote['elem_id']]['id'] = vote['elem_id']
        else:
            comments_rates[vote['elem_id']]['rate'] += vote['rate']
    del votes_comment
    comments = Comment.objects.filter(id__in=(comments_rates))
    for i in comments_rates:  # update rating on comments
        com = comments.get(id=i)
        com.rating += comments_rates[i]['rate']
        com.save()

    votes_post = cache.iter_keys('vote_post_*')
    posts_rates = {}
    for i in votes_post:
        vote = cache.get(i)
        cache.delete(i)
        if not vote['elem_id'] in posts_rates:
            posts_rates[vote['elem_id']] = {}
            posts_rates[vote['elem_id']]['category'] = vote['category']
            posts_rates[vote['elem_id']]['rate'] = vote['rate']
            posts_rates[vote['elem_id']]['id'] = vote['elem_id']
        else:
            posts_rates[vote['elem_id']]['rate'] += vote['rate']

    # cache.set('rating_post_day_' + today, posts, timeout=88000)
    del votes_post
    posts = Post.objects.filter(id__in=(posts_rates)).select_related('author')
    for i in posts_rates:  # update rating on posts
        post = posts.get(id=i)
        post.rating += posts_rates[i]['rate']
        post.author.rating += posts_rates[i]['rate'] / 30
        post.save()
        post.author.save()


@app.task(name="commentImage")
def commentImage(comment_id):
    data = Comment.objects.select_related('author').get(id=comment_id)

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
    return "Comment with id {} from user {} \
        proccessed".format(str(comment_id),
        str(data.author.username))


@app.task(name="addPost")
def addPost(post_id, tag_list, moderated):
    data = Post.objects.select_related().prefetch_related().get(id=post_id)
    nsfw = data.private
    have_new_tags = False
    data.tags.clear()
    tag = None
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
    if have_new_tags:
        cache.delete_pattern("taglist")

    if tag:
        data.main_tag = tag
    else:
        #tag = Tag.objects.get(id=8)
        tag, _ = Tag.objects.get_or_create(name="Разное")
        if _:
            tag.url = "others"
            tag.save()
        data.main_tag = tag

    # ищем картинки в тексте
    soup = srcsets(data.text, True, post_id=post_id)

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

    if data.post_image:

        post_image_file = sidebarThumbnail(data.post_image.path, data.id)
        data.post_thumbnail = stripMediaFromPath(post_image_file)

        data.main_image_srcset = srcsetThumb(data.post_image, post_id=data.id)
        # change post_image link to webm
        if not BeautifulSoup(data.main_image_srcset, "html5lib").video == None:
            post_image_file = BeautifulSoup(data.main_image_srcset, "html5lib")\
                                        .video.source['src']
        else:
            post_image_file = BeautifulSoup(data.main_image_srcset, "html5lib")\
                                        .img['src']
        data.post_image = stripMediaFromPath(post_image_file)

    if not moderated:
        data.status = "P"
    data.save()

    post = {}
    post['title'] = data.title
    post['url'] = data.get_absolute_url()
    post['author'] = data.author.id
    post['post'] = 1

    group = "add-post"
    Group(group).send({
        "text": json.dumps(post) })

    cache_str = "*page_" + str(data.category) + "*"
    cache.delete_pattern(cache_str)
    cache_str = "*post_single_" + str(data.id)
    cache.delete(cache_str)
