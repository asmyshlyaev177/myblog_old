import os
from celery import Celery
from celery.task import periodic_task
from celery.schedules import crontab
from django.conf import settings
from datetime import timedelta

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myblog.settings')

app = Celery('myblog')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

"""app.conf.beat_schedule = {
    'add-every-30-seconds': {
        'task': 'taglist',
        'schedule': 10.0,
        'args': ()
    },
}"""

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

app.conf.update(
    result_expires=60,
)

if __name__ == '__main__':
    app.start()
