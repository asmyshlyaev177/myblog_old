from celery import Celery
from celery.task import periodic_task
from datetime import timedelta
import os, datetime, json
from blog.models import Tag

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
