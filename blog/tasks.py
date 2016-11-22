from celery import Celery
from celery.task import periodic_task
from datetime import timedelta
import os, datetime, json
from .models import Post
from .models import RatingPost,RatingTag, Tag, Rating
from slugify import slugify, SLUG_OK

from time import gmtime, strftime

app = Celery('tasks', broker='pyamqp://guest@localhost//')


@app.task
def add(x, y):
    return x + y

#@periodic_task(run_every=timedelta(seconds=10))
@app.task()
def test(self):
    os.mknod(str(datetime.datetime.now()))

@app.task(name='taglist')
def taglist():
    tags = Tag.objects.all().values()
    data = []
    for i in tags:
        #tag = {}
        #tag['id'] = i['id']
        #tag['name'] = i['name']
        data.append(i['name'])
        filename = "/root/myblog/myblog/blog/static/taglist.json"
    with open(filename, 'w') as out:
        out.write(json.dumps(data))

@app.task(name="addPostTags")
def addPostTags(post_id, tag_list):
    data = Post.objects.get(id=post_id)
    j = True
    nsfw = data.private
    for i in tag_list:
        if len(i) > 2:
            if nsfw == True:
                tag_url = slugify(i.lower()+"_nsfw")
                tag, have_new_tags = Tag.objects.get_or_create(name=i,
                                      url=tag_url,
                                      private=nsfw)
                #tag = Tag.objects.get(name=i+"_nsfw")
            else:
                tag_url = slugify(i.lower())
                tag, have_new_tags = Tag.objects.get_or_create(name=i,
                                      url=tag_url )
            if have_new_tags:
                tag.save()
        #tag = Tag.objects.get(url=tag_url)
            data.tags.add(tag)
        if j:
            if tag.url != "" and tag.url != None:
                data.main_tag = tag.url
            else:
                data.main_tag = slugify("Разное".lower())
            j = False
        data.save()
        tag_rating, _ = RatingTag.objects.get_or_create(tag=tag)
        tag_rating.tag = tag
        tag_rating.rating = 0
        tag_rating.save()
        post_rating, _ = RatingPost.objects.get_or_create(post=data)
        post_rating.post = data
        if _:
            post_rating.rating = 0.0
        post_rating.save()
        if have_new_tags:
            taglist.delay()
