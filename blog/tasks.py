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
import datetime
#from django.utils import timezone
#from django.http import (HttpResponse,JsonResponse)
from urllib.request import urlopen, urlretrieve, Request

from time import gmtime, strftime

app = Celery('tasks', broker='pyamqp://guest@localhost//')


#@periodic_task(run_every=timedelta(seconds=10))
"""@app.task()
def test(self):
    os.mknod(str(datetime.datetime.now()))"""

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

@app.task(name="RatePost")
def RatePost(userid, postid, vote):

    post = Post.objects.get(id=postid)


    user = myUser.objects.get(id=userid)
    user_votes, notexist = UserVotes.objects.get_or_create(user=user)
    if user_votes.count != "B":

        if user_votes.count != "U":
            user_votes.votes -= 1
            user_votes.save()
        if user_votes.votes <= 0 and user_votes.count != "U":
            user.has_votes = False
            user.save()

        if post.rateable:
            v = VotePost(post=post, rate=vote, score= user_votes.weight)
            v.save()

@app.task(name="CalcPostRating")
def CalcPostRating():
    #another task
    delta = datetime.timedelta(hours=+3)
    tz = datetime.timezone(delta)

    dt = datetime.datetime.now(tz=tz)
    rt = datetime.timedelta(hours=-2)
    day = datetime.timedelta(hours=-24)
    week = datetime.timedelta(days=-7)
    month = datetime.timedelta(weeks=-4)
    two_month = datetime.timedelta(weeks=-8)
    end = dt

    vote_list = VotePost.objects.all()
    v = vote_list.values_list('post', flat=True).distinct()
    post_ids = set()
    for i in v:
        post_ids.add(i)

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
                votes_count += 1
                i.counted = True
                i.save()
            post_rating.votes += votes_count
            post_rating.rating += sum
            tag_rating.votes += votes_count
            tag_rating.rating += sum/50
            author_rating.rating += sum/50
            author_rating.votes += votes_count
            author_rating.save()
            rt_change = True

        #rating for day
        sum = 0.0
        start = dt + day
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
        start = dt + week
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
        start = dt + month
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
            tag_rating.save()

@app.task(name="userVotes")
def userVotes():
    usersVotes = UserVotes.objects.all()
    delta_tz = datetime.timedelta(hours=+3)
    tz = datetime.timezone(delta_tz)
    delta = datetime.timedelta(weeks=4)
    dt = datetime.datetime.now(tz=tz)
    for vote in usersVotes:
        if vote.count == "N" or vote.count == "B":
            user = vote.user
            if user.date_joined < dt - delta:
                coef = 0.25
                vote.votes = 20
            else:
                coef = 0.0
                vote.votes = 10

            user_rating = RatingUser.objects.get(user=user)
            vote.weight = 0.25 + coef + user_rating.rating/50
            user.has_votes = True
            print("User: " + str(user)+" weight "+str(vote.weight)+ " votes "+ str(vote.votes))
            user.save()
            vote.save()

@app.task(name="deleteOldVotes")
def deleteOldVotes():
    delta = datetime.timedelta(hours=+3)
    tz = datetime.timezone(delta)
    dt = datetime.datetime.now(tz=tz)

    dt = datetime.datetime.now()
    start = dt + datetime.timedelta(weeks=-96)
    end = dt + datetime.timedelta(weeks=-4, days=-3)
    VotePost.objects.all().filter(created__range=(start, end)).delete()

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
            pass
            #taglist.delay()
