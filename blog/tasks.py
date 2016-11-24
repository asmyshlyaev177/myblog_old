from celery import Celery
from celery.task import periodic_task
from datetime import timedelta
import os, datetime, json, re
from blog.models import Post
from blog.models import (RatingPost,RatingTag, Tag, Rating, Thumbnail, myUser,
                        UserVotes, RatingUser, VotePost)
from slugify import slugify, SLUG_OK
from bs4 import BeautifulSoup
from PIL import Image
from urllib.parse import urlparse, urlencode
from django.utils import timezone
import datetime
#from django.http import (HttpResponse,JsonResponse)
from urllib.request import urlopen, urlretrieve, Request

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
        data.append(i['name'])
    filename = "/root/myblog/myblog/blog/static/taglist.json"
    with open(filename, 'w', encoding='utf8') as out:
        out.write(json.dumps(data), ensure_ascii=False)

@app.task(name="RatePost")
def RatePost(userid, postid, vote):

    post = Post.objects.get(id=postid)
    if post.rateable == False:
        return ""
    user = myUser.objects.get(id=userid)

    user_votes, notexist = UserVotes.objects.get_or_create(user=user)
    user_votes.votes -= 1
    if user_votes.votes <= 0:
        user.has_votes = False
        user.save()

    user_votes.save()

    user_rating, notexist = RatingUser.objects.get_or_create(user=user)
    if notexist:
        user_rating.save()
    v = VotePost(post=post, rate=vote, score= user_votes.weight)
    v.save()

@app.task(name="CalcPostRating")
def CalcPostRating():
    #another task
    posts = Post.objects.filter(status="P").filter(rateable = True)
    dt = datetime.datetime.now()
    day = datetime.timedelta(hours=-24)
    week = datetime.timedelta(days=-7)
    month = datetime.timedelta(weeks=-4)
    two_month = datetime.timedelta(weeks=-8)
    end = dt

    for post in posts:

        post_rating, notexist = RatingPost.objects.get_or_create(post=post)

        #rating
        sum = 0.0
        votes_count = 0
        start = dt + day
        votes = VotePost.objects.filter(post=post).filter(created__range=(start, end))
        for i in votes:
            if i.rate == 0:
                sum -= i.score
            if i.rate == 1:
                sum += i.score
            votes_count += 1
        post_rating.votes += votes_count
        post_rating.rating += sum

        #rating for last week
        sum = 0.0
        start = dt + week
        votes = VotePost.objects.filter(post=post).filter(created__range=(start, end))
        for i in votes:
            if i.rate == 0:
                sum -= i.score
            if i.rate == 1:
                sum += i.score
        post_rating.week = sum

        #rating for last month
        sum = 0.0
        start = dt + month
        votes = VotePost.objects.filter(post=post).filter(created__range=(start, end))
        for i in votes:
            if i.rate == 0:
                sum -= i.score
            if i.rate == 1:
                sum += i.score
        post_rating.month = sum

        post_rating.save()

    #delete votes older than 2 month
    start = dt + datetime.timedelta(weeks=-96)
    end = dt + two_month


    VotePost.objects.filter(created__range=(start, end)).delete()

@app.task(name="addPost")
def addPost(post_id, tag_list):
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
            else:
                tag_url = slugify(i.lower())
                tag, have_new_tags = Tag.objects.get_or_create(name=i,
                                      url=tag_url )
            if have_new_tags:
                tag.save()
            data.tags.add(tag)
        if j:
            if tag.url != "" and tag.url != None:
                data.main_tag = tag
            else:
                t = Tag.objects.get(id=8)
                data.main_tag = t
            j = False

        """Resize img if it is bigger than thumb"""
        soup = BeautifulSoup(data.text) #текст поста
        img_links = soup.find_all("img") #ищем все картинки

        thumb_img_size = 640, 480

        if len(img_links) != 0:
            for i in img_links: # для каждой

				# находим ссылку и файл и вых. файл
                del i['style'] #удаляем стиль
                link = re.search(r"/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<file>\S*)\.(?P<ext>\w*)", str(i))
                file = '/root/myblog/myblog/blog/static/media/{}/{}/{}/{}.{}'\
                .format(link.group("year"), link.group("month"),link.group("day"),link.group("file"),link.group("ext"))
                file_out = '/root/myblog/myblog/blog/static/media/{}/{}/{}/{}-thumbnail.{}'\
                .format(link.group("year"), link.group("month"),link.group("day"),link.group("file"),link.group("ext"))
                if os.path.isfile(file):

					#i['class'] = img_class # присваиваем
                    i['class'] = 'responsive-img'
					# если картинка больше нужного размера создаём миниатюру
                    w,h = Image.open(file).size
                    if w > thumb_img_size[0]:

                        img = Image.open(file)
                        img.thumbnail(thumb_img_size)
                        img.save(file_out) # сохраняем
                        i['src'] = '/media/{}/{}/{}/{}-thumbnail.{}'.format(link.group("year"), link.group("month"),link.group("day"),link.group("file"),link.group("ext"))
                        a_tag = soup.new_tag("a")
                        # оборачиваем в ссылку на оригинал
                        a_tag['href'] = '/media/{}/{}/{}/{}.{}'.format(link.group("year"), link.group("month"),link.group("day"),link.group("file"),link.group("ext"))
                        a_tag['data-gallery'] = ""
                        i = i.wrap(a_tag)

		# выравниваем видео по центру

        ifr_links = soup.find_all("iframe")
        ifr_class = []
        if len(img_links) != 0:
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
