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
