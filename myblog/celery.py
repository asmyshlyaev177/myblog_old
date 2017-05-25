import json
import os
from celery import Celery
from celery.schedules import crontab
from kombu.serialization import register

register('json', json.dumps, json.loads, content_type='application/json',
         content_encoding='utf-8')
# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myblog.settings')

app = Celery('myblog',
             # backend='redis://Qvjuzowu177Qvjuzowu177Qvjuzowu177@127.0.0.1:6379/0',
             redis_host="127.0.0.1",
             redis_password="Qvjuzowu177Qvjuzowu177Qvjuzowu177",
             redis_db=0,
             redis_port=6379,
             result_serializer='json',
             broker_url='amqp://django:Qvjuzowu177Qvjuzowu177Qvjuzowu177@127.0.0.1:5672//',
             result_expires=120,
             result_backend='redis://',
             include=['blog.tasks'],
             task_time_limit=400
             )

app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'Post Rating everyhour': {
        'task': 'calc_rating',
        # 'schedule': 60.0, #3600
        'schedule': crontab(minute=30),
        'args': (),
    },
}

if __name__ == '__main__':
    app.start()
