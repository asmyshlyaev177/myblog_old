# -*- coding: utf-8 -*-
import os, json
from celery import Celery
from celery.task import periodic_task
from celery.schedules import crontab
from django.conf import settings
from datetime import timedelta
from kombu.serialization import register


register('json', json.dumps, json.loads, content_type='application/json',
         content_encoding='utf-8')
# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myblog.settings')

app = Celery('myblog')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.update(
    result_backend='redis://',
    backend='redis://',
    result_serializer='json',
    broker_url='pyamqp://guest:guest@127.0.0.1/',
    # broker_url='librabbitmq://guest:guest@localhost/',
    result_expires=120,
)

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'Post Rating everyhour': {
        'task': 'CalcRating',
        # 'schedule': 60.0, #3600
        'schedule': crontab(minute=30),
        'args': (),
    },

}


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

if __name__ == '__main__':
    app.start()
