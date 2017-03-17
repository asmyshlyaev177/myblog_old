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
from django.utils.encoding import uri_to_iri, iri_to_uri
from urllib.request import urlopen, Request
from blog.functions import (srcsets, srcsetThumb, saveImage,
                            stripMediaFromPath,
                           findLink, findFile)
from django.core.cache import cache
from channels import Group
from myblog.celery import app

delta_tz = datetime.timedelta(hours=+3)
tz = datetime.timezone(delta_tz)


@app.task(name="Rate")
def Rate(userid, date_joined, votes_type, type, elem_id, vote):
    """
    Оценка постов и комментов
    """
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
        if votes_type == "N":
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
    """
    Подсчёт рейтинга постов, комментов и юзеров
    """
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
        comment = comments.get(id=i)
        cache_str = "comment_" + str(comment.post.id)
        cache.delete(cache_str)
        comment.rating += comments_rates[i]['rate']
        comment.save()

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
    for post_id in posts_rates:  # update rating on posts
        post = posts.get(id=post_id)
        post.rating += posts_rates[post_id]['rate']
        post.author.rating += posts_rates[post_id]['rate'] / 30
        post.save()
        post.author.save()
        cache_str = "page_" + str(post.category.slug) + "_*"
        cache.delete_pattern(cache_str)
    cache.delete_pattern("page_None_*")
    cache.delete_pattern("good_posts_*")


@app.task(name="commentImage")
def commentImage(comment_id):
    """
    Конвертирование картинок в комментах
    """
    comment_raw = Comment.objects.select_related('author').get(id=comment_id)
    soup = srcsets(comment_raw.text, True)
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
    comment_raw.text = soup.prettify()
    comment_raw.save()

    cache_str = "comment_" + str(comment_raw.post.id)
    cache.delete(cache_str)
    cache_str= "count_comments_" + str(comment_raw.post.id)
    cache.delete(cache_str)

    comment = {}
    comment['id'] = comment_raw.id
    if comment_raw.parent:
        comment['parent'] = comment_raw.parent.id
    comment['author'] = comment_raw.author.username
    if comment_raw.author.avatar:
        comment['avatar'] = comment_raw.author.avatar.url
    else:
        comment['avatar'] = "/media/avatars/admin/avatar.jpg"

    if comment_raw.level != 0:
        comment['parent'] = comment_raw.parent.id
    else:
        comment['parent'] = 0
    comment['text'] = comment_raw.text
    comment['level'] = comment_raw.level
    comment['comment'] = 1
    comment['created'] = (comment_raw.created + delta_tz).strftime('%Y.%m.%d %H:%M')
    group = comment_raw.post.get_absolute_url().strip('/').split('/')[-1]
    Group(group).send({
        # "text": "[user] %s" % message.content['text'],
        "text": json.dumps(c),
                        })
    return "Comment with id {} from user {} \
        proccessed".format(str(comment_id),
        str(comment_raw.author.username))


@app.task(name="addPost")
def addPost(post_id, tag_list, moderated, group=None):
    """
    Обработка поста при добавлении
    Тэги, сжатие и конвертация изображений и т.д.
    Пост_id, лист тэгов, разрешение добавлять посты без проверки
    и группу куда прислать уведомление о добавлении через сокет(при редактировании)
    """
    post_raw = Post.objects.select_related().prefetch_related().get(id=post_id)
    nsfw = post_raw.private
    have_new_tags = False
    post_raw.tags.clear()
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
            post_raw.tags.add(tag)
    if have_new_tags:
        cache.delete_pattern("taglist")

    if tag:
        post_raw.main_tag = tag
    else:
        #tag = Tag.objects.get(id=8)
        tag, _ = Tag.objects.get_or_create(name="Разное")
        if _:
            tag.url = "others"
            tag.save()
        post_raw.main_tag = tag

    # ищем картинки в тексте
    soup = srcsets(post_raw.text, True, post_id=post_id)

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
    post_raw.text = soup.prettify()

    # image from url

    if post_raw.image_url:
        today = datetime.date.today()
        upload_path1 = '/root/myblog/myblog/blog/static/media/' + \
        str(today.year) + '/' + str(today.month) + '/' + str(today.day) + '/'
        upload_path = str(today.year) + '/' + str(today.month) + \
                                        '/' + str(today.day) + '/'
        filename = urlparse(post_raw.image_url).path.split('/')[-1]
        save_path = os.path.join(upload_path1, filename)
        user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
        headers = {'User-Agent': user_agent}
        browser_headers = {'name': 'Alex',
                      'location': 'Moscow', }
        data = urlencode(browser_headers)
        data = data.encode('ascii')

        try:
            req = Request(post_raw.image_url, data, headers, method="GET")
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            with urlopen(req, timeout=7) as response, open(save_path, 'wb') as out_file:
                data = response.read()
                out_file.write(data)
            post_raw.post_image = os.path.join(upload_path, filename)
        except:
            pass
        post_raw.image_url = ""

    if post_raw.post_image:
        post_raw.main_image_srcset = srcsetThumb(post_raw.post_image, post_id=post_raw.id)
        # change post_image link to webm
        if not BeautifulSoup(post_raw.main_image_srcset, "html5lib").video == None:
            post_image_file = BeautifulSoup(post_raw.main_image_srcset, "html5lib")\
                                        .video.source['src']
            post_raw.post_image = stripMediaFromPath(post_image_file)
        else:
            soup = BeautifulSoup(post_raw.main_image_srcset, "html5lib")\
                    .img['src']
            link = findLink(iri_to_uri(soup))
            file = uri_to_iri(findFile(link))
            post_image_file = saveImage(link, file, 150, h=150)
        post_raw.post_thumbnail = stripMediaFromPath(post_image_file)

    if not moderated:
        post_raw.status = "P"
    post_raw.save()

    post = {}
    post['title'] = post_raw.title
    post['url'] = post_raw.get_absolute_url()
    post['author'] = post_raw.author.id
    post['id'] = post_raw.id
    post['post'] = 1

    if not group:
        group = "add-post"
    Group(group).send({
        "text": json.dumps(post) })

    cache_str = ["*page_" + str(post_raw.category) + "*",
                 "*page_None*",
                "*good_posts_" + str(post_raw.category) + "_*",
                 "*good_posts_None_*",
                 "*post_single_" + str(post_raw.id)+"*"
                ]
    for i in cache_str:
        cache.delete_pattern(i)
